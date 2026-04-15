import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
# 在文件开头补充导入混合精度模块
from scipy.interpolate import griddata

# ==========================================
# 全局配置
# ==========================================
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
torch.manual_seed(42)
np.random.seed(42)
print(f"当前计算设备: {DEVICE}")

def to_np(t):
    if isinstance(t, np.ndarray): return t
    return t.detach().cpu().numpy()

# PINN 物理核心 (增强版 RNN)
# ==========================================
class MaterialSurrogate(nn.Module):
    # 每个材料参数（导热系数k、热容Cp、密度Rho、弹性模量E、热膨胀系数Al、屈服强度Yld、泊松比Nu）
    #      
    def __init__(self, name="Prop", default_val=1.0):
        super().__init__()
        self.name = name
        self.net = nn.Sequential(
            nn.Linear(1, 128), nn.Tanh(), 
            nn.Linear(128, 128), nn.Tanh(), 
            nn.Linear(128, 128), nn.Tanh(),
            nn.Linear(128, 1)
        )
        self.register_buffer('const', torch.tensor(float(default_val)))
        self.register_buffer('internal_scale', torch.tensor(1.0)) 
        self.register_buffer('t_scale', torch.tensor(2500.0))
        self.use_curve = False 

    def set_constant(self, val):
        self.use_curve = False
        self.const.fill_(float(val))

    def forward(self, T):
        ui_coeff = self.const.item()
        if self.use_curve:
            raw_val = self.net(T / self.t_scale) * self.internal_scale
            return ui_coeff * raw_val
        else:
            return torch.full_like(T, ui_coeff)

    def fit(self, T, Y):
        if len(T) < 2: 
            self.set_constant(np.mean(Y))
            return 0.0, np.mean(Y)
        self.use_curve = True
        max_abs_val = np.max(np.abs(Y))
        if max_abs_val < 1e-15: max_abs_val = 1.0
        self.internal_scale.fill_(max_abs_val)
        self.const.fill_(1.0) 
        max_t = np.max(T)
        scale_t = float(max_t) if max_t > 100.0 else 2500.0
        self.t_scale.fill_(scale_t)
        Tt = torch.tensor(T, dtype=torch.float32).view(-1, 1).to(DEVICE)
        Y_target = torch.tensor(Y / max_abs_val, dtype=torch.float32).view(-1, 1).to(DEVICE)
        opt = torch.optim.AdamW(self.parameters(), lr=0.005) 
        scheduler = torch.optim.lr_scheduler.StepLR(opt, step_size=2000, gamma=0.5)
        criterion = nn.HuberLoss(delta=0.1)
        self.train(); self.to(DEVICE)
        final_loss = 0.0
        for i in range(8000): 
            opt.zero_grad()
            pred_norm = self.net(Tt / self.t_scale)
            loss = criterion(pred_norm, Y_target)
            loss.backward()
            opt.step()
            scheduler.step() 
            final_loss = loss.item()
        self.eval()
        return final_loss, 1.0

class WeldingDNN(nn.Module):
    def __init__(self, din, dout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(din, 80), nn.Tanh(), nn.Linear(80, 80), nn.Tanh(),
            nn.Linear(80, 80), nn.Tanh(), nn.Linear(80, 80), nn.Tanh(), nn.Linear(80, dout)
        )
        
    def forward(self, x): 
        # [核心修改]：用 softplus 锁死网络输出的底线，确保其严格大于 0
        return torch.nn.functional.softplus(self.net(x))

# [全新模块] 用于学习塑性路径依赖记忆的 LSTM 模型
class WeldingRNN(nn.Module):
    # 使用LSTM捕捉时间序列信息，因为材料变形依赖于整个热历史，而不仅是当前时刻的状态
    def __init__(self, din, dout, hidden=128, num_layers=2):
        super().__init__()
        # batch_first=True 保证输入形状为 (Batch, SeqLen, Features)
        self.lstm = nn.LSTM(din, hidden, num_layers, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden, 80), nn.Tanh(), 
            nn.Linear(80, dout)
        )
    def forward(self, x):
        # x 形状: (Batch, SeqLen, Features)
        out, _ = self.lstm(x)
        # 经过全连接层后返回完整的序列预测 (Batch, SeqLen, Dout)
        return self.fc(out) 

class LaserWeldingPINN:
    def __init__(self):
        self.lb = torch.zeros(8).to(DEVICE); self.ub = torch.ones(8).to(DEVICE)
        self.eff = 0.75
        self.weld_duration = 1000.0 
        self.T0 = 20.0
        self.fixed_nodes = None
        self.seq_len = 16 # [新增] LSTM 的时间记忆步数 (设为8平衡精度和显存)
        
        # 温度用传统 DNN (空间点独立计算 PDE)
        self.net_temp = WeldingDNN(8, 1).to(DEVICE)
        # [修改] 位移用 RNN (输入维度 13, 输出维度 3)
        self.net_disp = WeldingRNN(13, 3).to(DEVICE)
        
        self.mk = MaterialSurrogate("k", 45.0).to(DEVICE)
        self.mCp = MaterialSurrogate("Cp", 500e6).to(DEVICE)
        self.mRho = MaterialSurrogate("Rho", 7800).to(DEVICE)
        self.mE = MaterialSurrogate("E", 2e5).to(DEVICE)
        self.mAl = MaterialSurrogate("Al", 1e-5).to(DEVICE)
        self.mYld = MaterialSurrogate("Yld", 300).to(DEVICE)
        self.mNu = MaterialSurrogate("Nu", 0.3).to(DEVICE)
        
        params = list(self.net_temp.parameters()) + list(self.net_disp.parameters())
        self.opt = torch.optim.Adam(params, lr=1e-3)

    def set_fixed_nodes(self, pts):
        if pts is not None: self.fixed_nodes = torch.tensor(pts, dtype=torch.float32).to(DEVICE)
        else: self.fixed_nodes = None

    def normalize(self, x): 
        # 归一化
        denom = self.ub - self.lb; denom[denom < 1e-6] = 1.0
        return 2.0 * (x - self.lb) / denom - 1.0

    def hybrid_source(self, x,y,z,t, P,v,r,d):
        # 热源模型的定义
        z_c = v*t; r_sq = x**2 + (z - z_c)**2
        Pe = P * self.eff
        fv = (2.1 * Pe / (np.pi*d*(r**2+1e-8))) * torch.exp(-3*r_sq/(r**2+1e-8))
        myv = torch.sigmoid(50*(y-(3.0-d))) * torch.sigmoid(50*(3.0-y))
        fs = (0.9 * Pe / (np.pi*(0.2*d)*(r**2+1e-8))) * torch.exp(-3*r_sq/(r**2+1e-8))
        mys = torch.sigmoid(50*(y-(3.0-0.2*d))) * torch.sigmoid(50*(3.0-y))
        mt = torch.sigmoid(100*(self.weld_duration - t)) 
        return (fv*myv + fs*mys) * mt

    def compute_bc_loss(self):
        # 对于固定节点（例如夹具约束点），强制其位移为0。
        # 通过随机采样时间和固定节点坐标，输入位移网络，计算预测位移的平方均值作为损失。
        if self.fixed_nodes is None: return torch.tensor(0.0).to(DEVICE)
        pts = self.fixed_nodes; n = pts.shape[0]
        t = torch.rand(n, 1).to(DEVICE) * self.weld_duration
        p = torch.full((n,1), (self.ub[4]+self.lb[4])/2).to(DEVICE)
        v = torch.full((n,1), (self.ub[5]+self.lb[5])/2).to(DEVICE)
        r = torch.full((n,1), (self.ub[6]+self.lb[6])/2).to(DEVICE)
        d = torch.full((n,1), (self.ub[7]+self.lb[7])/2).to(DEVICE)
        
        inp = torch.cat([pts, t, p, v, r, d], dim=1)
        bs = inp.shape[0]
        
        # [修改] 构建序列验证边界条件
        steps = torch.linspace(0.0, 1.0, self.seq_len).view(1, -1, 1).to(DEVICE)
        t_seq = inp[:,3:4].unsqueeze(1) * steps
        xyz_seq = inp[:,0:3].unsqueeze(1).expand(-1, self.seq_len, -1)
        params_seq = inp[:,4:8].unsqueeze(1).expand(-1, self.seq_len, -1)
        batch_seq_flat = torch.cat([xyz_seq, t_seq, params_seq], dim=2).view(bs * self.seq_len, 8)
        
        self.net_temp.eval()
        with torch.no_grad(): # 其实这里之前加了 no_grad，但为了保险和统一，建议按下面的写法
            Tp_seq = self.net_temp(self.normalize(batch_seq_flat))
            
        # ==========================================
        # 这里也一定要加上 .detach() ！！！
        # ==========================================
        T_seq = (Tp_seq * 2500.0 + self.T0).detach() 
        
        e = self.mE(T_seq); al = self.mAl(T_seq); yld = self.mYld(T_seq); nu = self.mNu(T_seq)
        feats = torch.cat([(T_seq - self.T0)/2500.0, e/2e5, al*1e5, yld/500.0, nu], 1)
        
        rnn_input = torch.cat([self.normalize(batch_seq_flat), feats], 1).view(bs, self.seq_len, 13)
        Up_seq = self.net_disp(rnn_input)
        Up_last = Up_seq[:, -1, :] 
        
        return torch.mean(Up_last**2)

    def compute_loss(self, batch, target, return_pde_res_only=False):
        batch.requires_grad_(True)
        bs = batch.shape[0]
        x,y,z,t = batch[:,0:1], batch[:,1:2], batch[:,2:3], batch[:,3:4]
        p,v,r,d = batch[:,4:5], batch[:,5:6], batch[:,6:7], batch[:,7:8]
        
        # ==========================================
        # 1. 纯 FP32 计算温度场与 PDE 
        # ==========================================
        Tp = self.net_temp(self.normalize(batch)) 
        T = Tp * 2500.0 + self.T0
        k = self.mk(T); cp = self.mCp(T); rho = self.mRho(T)
        
        grads = torch.autograd.grad(T, batch, torch.ones_like(T), create_graph=True)[0]
        Tt = grads[:,3:4]
        qx, qy, qz = k*grads[:,0:1], k*grads[:,1:2], k*grads[:,2:3]
        
        div = torch.autograd.grad(qx, batch, torch.ones_like(qx), create_graph=True)[0][:,0:1] + \
              torch.autograd.grad(qy, batch, torch.ones_like(qy), create_graph=True)[0][:,1:2] + \
              torch.autograd.grad(qz, batch, torch.ones_like(qz), create_graph=True)[0][:,2:3]
        
        Q = self.hybrid_source(x,y,z,t, p,v,r,d)
        res_heat = rho*cp*Tt - div - Q
        
        if return_pde_res_only:
            return torch.abs(res_heat).detach()
        
        norm_factor = torch.max(torch.abs(Q)).detach() + 1e6
        res_heat_norm = res_heat / norm_factor
        l_pde = torch.nn.functional.smooth_l1_loss(res_heat_norm, torch.zeros_like(res_heat_norm), beta=0.1)
        
        # ==========================================
        # 2. RNN 序列与位移场
        # ==========================================
        from torch.cuda.amp import autocast
        steps = torch.linspace(0.0, 1.0, self.seq_len).view(1, -1, 1).to(DEVICE)
        t_seq = t.unsqueeze(1) * steps 
        xyz_seq = batch[:,0:3].unsqueeze(1).expand(-1, self.seq_len, -1)
        params_seq = batch[:,4:8].unsqueeze(1).expand(-1, self.seq_len, -1)
        
        batch_seq = torch.cat([xyz_seq, t_seq, params_seq], dim=2) 
        batch_seq_flat = batch_seq.view(bs * self.seq_len, 8)
        
        with autocast(enabled=True):
            Tp_seq_half = self.net_temp(self.normalize(batch_seq_flat))
            
        Tp_seq = Tp_seq_half.float()
        T_seq = (Tp_seq * 2500.0 + self.T0).detach() 
        
        e_seq = self.mE(T_seq); al_seq = self.mAl(T_seq); yld_seq = self.mYld(T_seq); nu_seq = self.mNu(T_seq)
        feats_seq = torch.cat([(T_seq-self.T0)/2500.0, e_seq/2e5, al_seq*1e5, yld_seq/500.0, nu_seq], 1)
        
        rnn_input_flat = torch.cat([self.normalize(batch_seq_flat), feats_seq], 1)
        rnn_input = rnn_input_flat.view(bs, self.seq_len, 13)
        
        with autocast(enabled=True):
            Up_seq_half = self.net_disp(rnn_input)
            
        Up_last = Up_seq_half.float()[:, -1, :] 
        
        # ==========================================
        # 3. 数据驱动 Loss 计算 (极值刺客：误差追杀法)
        # ==========================================
        T_target_norm = (target[:, 0:1] - self.T0) / 2500.0
        l_data_T = torch.mean((Tp - T_target_norm)**2)
        
        # 获取所有节点的 MSE (平方误差) 和 L1 (绝对误差)
        mse_u_nodes = torch.sum((Up_last - target[:, 1:4])**2, dim=1)
        l1_err_nodes = torch.sum(torch.abs(Up_last - target[:, 1:4]), dim=1)
        
        # 1. 基础盘：均方误差，维持那 99% 冷区 0.009mm 的极高精度
        l_data_u_base = torch.mean(mse_u_nodes)
        
        # ------------------------------------------
        # 2. 核心绝杀：最差样本 L1 强迫纠正
        # 不管这个点是不是在端部，只要当前这步它错得最离谱，就重锤它！
        # ------------------------------------------
        # 找出当前 Batch 中【绝对误差最大】的前 1% 节点 (最少 5 个)
        k_worst = max(int(bs * 0.01), 5)
        worst_errors, _ = torch.topk(l1_err_nodes, k=k_worst)
        
        # 为什么用 L1？因为当误差缩小到 0.05 时，MSE 的梯度会极度衰减，
        # 而 L1 无论误差多小，都能提供恒定不变的强力推力，死死把误差往下压！
        l_data_u_worst = torch.mean(worst_errors)
        
        # ------------------------------------------
        # 3. 终极组装
        # l_data_u_base 量级极小 (约 1e-4)，乘 100.0 提权使其不被忽略
        # l_data_u_worst 是绝对值量级 (约 0.1)，乘 1.0 刚好主导大误差的修正方向
        # ------------------------------------------
        l_data_U = l_data_u_base * 100.0 + l_data_u_worst * 1.0
        
        return l_pde, l_data_T, l_data_U
    
    def predict(self, x_in, batch_size=10000): # 为了防止 RNN 序列过大爆显存，调小了 batch_size
        self.net_temp.eval(); self.net_disp.eval()
        T_results = []; U_results = []
        n_samples = x_in.shape[0]
        with torch.no_grad():
            for i in range(0, n_samples, batch_size):
                batch_x = x_in[i : i + batch_size]
                bs = batch_x.shape[0]
                
                # 当前时刻的温度
                Tp = self.net_temp(self.normalize(batch_x))
                T_val = Tp * 2500.0 + self.T0
                T_results.append(T_val.cpu())
                
                # [新增] 还原当前点的历史位移累积路径
                steps = torch.linspace(0.0, 1.0, self.seq_len).view(1, -1, 1).to(DEVICE)
                t_seq = batch_x[:,3:4].unsqueeze(1) * steps
                xyz_seq = batch_x[:,0:3].unsqueeze(1).expand(-1, self.seq_len, -1)
                params_seq = batch_x[:,4:8].unsqueeze(1).expand(-1, self.seq_len, -1)
                
                batch_seq = torch.cat([xyz_seq, t_seq, params_seq], dim=2).view(bs * self.seq_len, 8)
                
                Tp_seq = self.net_temp(self.normalize(batch_seq))
                T_seq = Tp_seq * 2500.0 + self.T0
                
                e = self.mE(T_seq); al = self.mAl(T_seq); yld = self.mYld(T_seq); nu = self.mNu(T_seq)
                feats = torch.cat([(T_seq - self.T0)/2500.0, e/2e5, al*1e5, yld/500.0, nu], 1)
                
                rnn_input = torch.cat([self.normalize(batch_seq), feats], 1).view(bs, self.seq_len, 13)
                Up_seq = self.net_disp(rnn_input)
                
                # 提取序列最后一个点作为最终预测值
                U_results.append(Up_seq[:, -1, :].cpu())
                
        return torch.cat(T_results, 0), torch.cat(U_results, 0)