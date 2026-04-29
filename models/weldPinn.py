import os
import torch
import torch.nn as nn
import numpy as np
import pandas as pd

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class PINNDataProcessor:
    def __init__(self):
        self.feature_cols = ['X', 'Y', 'Z', 'Time', 'Power', 'Speed', 'Radius', 'Depth']
        self.target_cols = ['Temperature', 'Disp_X', 'Disp_Y', 'Disp_Z']
        self.bounds = {} 

    def calc_displacement(self, df):
        if 'Disp_X' in df.columns: return df
        try:
            df = df.sort_values(by=['Node_ID', 'Time'])
            base_df = df[df['Time'] == 0.0][['Node_ID', 'X', 'Y', 'Z']].set_index('Node_ID')
            df_merged = df.join(base_df, on='Node_ID', rsuffix='_base')
            df['Disp_X'] = df_merged['X'] - df_merged['X_base']
            df['Disp_Y'] = df_merged['Y'] - df_merged['Y_base']
            df['Disp_Z'] = df_merged['Z'] - df_merged['Z_base']
            df.fillna(0, inplace=True)
        except: pass 
        return df

    def process_files(self, file_paths, is_training=True):
        print(f"[-] 正在读取 {len(file_paths)} 个文件...")
        all_data = []
        for fp in file_paths:
            try:
                # ==========================================
                # 【修改点1】：智能判断文件后缀，支持 Parquet 和 CSV
                # ==========================================
                if fp.endswith('.parquet'):
                    df = pd.read_parquet(fp)
                else:
                    df = pd.read_csv(fp)
                    
                if 'Temp' in df.columns and 'Temperature' not in df.columns:
                    df.rename(columns={'Temp': 'Temperature'}, inplace=True)
                df = self.calc_displacement(df)
                
                defaults = {'Power': 4800, 'Speed': 30, 'Radius': 0.5, 'Depth': 3.0}
                for col, val in defaults.items():
                    if col not in df.columns: df[col] = val
                
                if df['Power'].mean() < 100: 
                    # print(f"提示: 文件 {os.path.basename(fp)} 功率数值较小，可能是 kW/J，已自动转为 W/mJ")
                    df['Power'] *= 1000.0

                if all(c in df.columns for c in self.feature_cols + ['Temperature']):
                    all_data.append(df)
            except Exception as e:
                print(f" [-] 读取错误 {fp}: {e}")

        # ==========================================
        # 【修改点2】：返回 3 个 None，防止外层 unpack 报错
        # ==========================================
        if not all_data: 
            return None, None, None
            
        full_df = pd.concat(all_data, ignore_index=True)

        if is_training:
            print("[-] 执行奇异点削减 (Top 0.1%)...")
            clip_cols = ['Temperature', 'Disp_X', 'Disp_Y', 'Disp_Z']
            valid_cols = [c for c in clip_cols if c in full_df.columns]
            if valid_cols:
                lower = full_df[valid_cols].quantile(0.001)
                upper = full_df[valid_cols].quantile(0.999)
                full_df[valid_cols] = full_df[valid_cols].clip(lower=lower, upper=upper, axis=1)
            
            self.bounds['lb'] = full_df[self.feature_cols].min().values
            self.bounds['ub'] = full_df[self.feature_cols].max().values
            print("[-] 数据清洗完成")

        X_tensor = torch.tensor(full_df[self.feature_cols].values, dtype=torch.float32).to(DEVICE)
        Y_vals = []
        for col in self.target_cols:
            if col in full_df.columns: Y_vals.append(full_df[col].values)
            else: Y_vals.append(np.zeros(len(full_df)))
        Y_tensor = torch.tensor(np.column_stack(Y_vals), dtype=torch.float32).to(DEVICE)
        
        return X_tensor, Y_tensor, full_df

# ==========================================
# 1. 神经网络组件 (完全保留你的原始网络结构)
# ==========================================
class MaterialSurrogate(nn.Module):
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
            return ui_coeff * (self.net(T / self.t_scale) * self.internal_scale)
        return torch.full_like(T, ui_coeff)

    def fit(self, T, Y):
        """引擎动态拟合材料属性曲线"""
        if len(T) < 2: return
        self.use_curve = True
        max_abs_val = np.max(np.abs(Y))
        if max_abs_val < 1e-15: max_abs_val = 1.0
        self.internal_scale.fill_(max_abs_val)
        self.const.fill_(1.0) 
        max_t = np.max(T)
        self.t_scale.fill_(float(max_t) if max_t > 100.0 else 2500.0)
        
        Tt = torch.tensor(T, dtype=torch.float32).view(-1, 1).to(DEVICE)
        Y_target = torch.tensor(Y / max_abs_val, dtype=torch.float32).view(-1, 1).to(DEVICE)
        opt = torch.optim.AdamW(self.parameters(), lr=0.005) 
        criterion = nn.HuberLoss(delta=0.1)
        
        self.train(); self.to(DEVICE)
        for _ in range(3000): 
            opt.zero_grad()
            loss = criterion(self.net(Tt / self.t_scale), Y_target)
            loss.backward()
            opt.step()
        self.eval()

class WeldingDNN(nn.Module):
    def __init__(self, din, dout):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(din, 80), nn.Tanh(), nn.Linear(80, 80), nn.Tanh(),
            nn.Linear(80, 80), nn.Tanh(), nn.Linear(80, 80), nn.Tanh(), nn.Linear(80, dout)
        )
    def forward(self, x): 
        return torch.nn.functional.softplus(self.net(x))

class WeldingRNN(nn.Module):
    def __init__(self, din, dout, hidden=128, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(din, hidden, num_layers, batch_first=True)
        self.fc = nn.Sequential(nn.Linear(hidden, 80), nn.Tanh(), nn.Linear(80, dout))
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out)

# ==========================================
# 2. PINN 核心类 (剥离了 GUI)
# ==========================================
class LaserWeldingPINN:
    def __init__(self):
        self.lb = torch.zeros(8).to(DEVICE)
        self.ub = torch.ones(8).to(DEVICE)
        self.eff = 0.75
        self.weld_duration = 1000.0 
        self.T0 = 20.0
        self.fixed_nodes = None
        self.seq_len = 16 
        
        self.net_temp = WeldingDNN(8, 1).to(DEVICE)
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

    def normalize(self, x): 
        denom = self.ub - self.lb
        denom[denom < 1e-6] = 1.0
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
    
    def setup_materials_from_db(self, materials_list):
        """【新增】接收数据库查出的材料JSON列表，融合拟合"""
        mat_map = {
            'mk': self.mk, 'mCp': self.mCp, 'mRho': self.mRho,
            'mE': self.mE, 'mAl': self.mAl, 'mYld': self.mYld, 'mNu': self.mNu
        }
        for mat in materials_list:
            props = mat.properties # 这是数据库取出的 JSON 字典
            for key, surrogate in mat_map.items():
                if key in props:
                    data = props[key]
                    T = np.array([p[0] for p in data])
                    Y = np.array([p[1] for p in data])
                    surrogate.fit(T, Y) # 动态让模型认识这些材料的物性

# ==========================================
# 2. 对外提供的高层 API (推断引擎)
# ==========================================
class PINNInferenceEngine:
    def __init__(self, model_path: str):
        print(f"[*] 正在初始化并加载模型权重: {model_path}")
        self.pinn = LaserWeldingPINN()
        checkpoint = torch.load(model_path, map_location=DEVICE)
        self.pinn.net_temp.load_state_dict(checkpoint['nt'])
        self.pinn.net_disp.load_state_dict(checkpoint['nd'])
        self.pinn.lb = checkpoint['lb'].to(DEVICE)
        self.pinn.ub = checkpoint['ub'].to(DEVICE)

    def setup_material(self, properties_json: dict):
        """【核心突破】读取数据库 JSON 并动态注入物性，让模型认识新材料"""
        mat_map = {
            'mk': self.pinn.mk, 'mCp': self.pinn.mCp, 'mRho': self.pinn.mRho,
            'mE': self.pinn.mE, 'mAl': self.pinn.mAl, 'mYld': self.pinn.mYld, 'mNu': self.pinn.mNu
        }
        for key, surrogate in mat_map.items():
            if key in properties_json:
                data = properties_json[key]
                T = np.array([p[0] for p in data])
                Y = np.array([p[1] for p in data])
                surrogate.fit(T, Y)

    def predict_cloud(self, grid_pts: np.ndarray, params: dict):
        """接收三维网格，返回温度场和位移场的云图数据"""
        n = grid_pts.shape[0]
        inp = np.zeros((n, 8))
        inp[:, 0:3] = grid_pts
        inp[:, 3] = params['Time']
        inp[:, 4] = params['Power']
        inp[:, 5] = params['Speed']
        inp[:, 6] = params['Radius']
        inp[:, 7] = params['Depth']
        
        inp_tensor = torch.tensor(inp, dtype=torch.float32).to(DEVICE)
        T_res, U_res = self.pinn.predict(inp_tensor)
        
        return {
            "temp": T_res.flatten().tolist(),
            "ux": U_res[:, 0].tolist(),
            "uy": U_res[:, 1].tolist(),
            "uz": U_res[:, 2].tolist()
        }

# ==========================================
# 3. 内存管理：模型单例缓存池
# ==========================================
class ModelManager:
    _pool = {}

    @classmethod
    def get_engine(cls, model_path: str) -> PINNInferenceEngine:
        if model_path not in cls._pool:
            cls._pool[model_path] = PINNInferenceEngine(model_path)
        return cls._pool[model_path]

