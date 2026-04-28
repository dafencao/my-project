import torch
import torch.nn as nn
import numpy as np

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

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
        
        self.train()
        self.to(DEVICE)
        for _ in range(3000): # 推理前快速重载拟合 (可适当减少步数以提升接口响应速度)
            opt.zero_grad()
            loss = criterion(self.net(Tt / self.t_scale), Y_target)
            loss.backward()
            opt.step()
        self.eval()

    def forward(self, T):
        ui_coeff = self.const.item()
        if self.use_curve:
            return ui_coeff * (self.net(T / self.t_scale) * self.internal_scale)
        return torch.full_like(T, ui_coeff)

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

class LaserWeldingPINN:
    def __init__(self):
        self.lb = torch.zeros(8).to(DEVICE)
        self.ub = torch.ones(8).to(DEVICE)
        self.T0 = 20.0
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

    def normalize(self, x): 
        denom = self.ub - self.lb
        denom[denom < 1e-6] = 1.0
        return 2.0 * (x - self.lb) / denom - 1.0

    def predict(self, x_in, batch_size=5000):
        self.net_temp.eval(); self.net_disp.eval()
        T_results = []; U_results = []
        n_samples = x_in.shape[0]
        
        with torch.no_grad():
            for i in range(0, n_samples, batch_size):
                batch_x = x_in[i : i + batch_size]
                bs = batch_x.shape[0]
                
                Tp = self.net_temp(self.normalize(batch_x))
                T_val = Tp * 2500.0 + self.T0
                T_results.append(T_val.cpu().numpy())
                
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
                U_results.append(Up_seq[:, -1, :].cpu().numpy())
                
        return np.concatenate(T_results, axis=0), np.concatenate(U_results, axis=0)

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