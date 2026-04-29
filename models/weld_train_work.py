import os
import torch
import datetime
import numpy as np
import pandas as pd
from torch.cuda.amp import GradScaler
from models.Wdata_manage import WProcessRecord
from models.w_pred_model import TrainedModel
from models.material import Material
from models.weldPinn import LaserWeldingPINN, DEVICE
from models.weldPinn import PINNDataProcessor

DATA_ROOT = r"E:\welding_data"

def background_train_task(
    joint_id: int, 
    method_id: int, 
    model_version: str, 
    description: str,
    epochs: int = 15000
):
    print(f"[*] 启动后台训练任务: 接头={joint_id}, 方法={method_id}")
    
    # ==========================================
    # 1. 从数据库检索训练和验证数据集
    # 【修改点2】：去掉 await，使用标准的 Peewee 同步查询语法
    # ==========================================
    train_records = list(WProcessRecord.select().where(
        (WProcessRecord.joint_id == joint_id) & 
        (WProcessRecord.method_id == method_id) & 
        (WProcessRecord.dataset_type == 'train')
    ))
    
    val_records = list(WProcessRecord.select().where(
        (WProcessRecord.joint_id == joint_id) & 
        (WProcessRecord.method_id == method_id) & 
        (WProcessRecord.dataset_type == 'val')
    ))
    
    if not train_records:
        print("[-] 错误：该工况下无训练数据。")
        return

    train_files = [os.path.join(DATA_ROOT, r.file_path) for r in train_records]
    val_files = [os.path.join(DATA_ROOT, r.file_path) for r in val_records]
    
    # 溯源材料 ID 列表并查询物性数据
    material_ids = list(set([r.material_id for r in train_records]))
    materials = list(Material.select().where(Material.id.in_(material_ids)))

    # ==========================================
    # 2. 数据加载与模型初始化
    # ==========================================
    processor = PINNDataProcessor()
    X_train, Y_train, _ = processor.process_files(train_files, is_training=True)
    
    model = LaserWeldingPINN()
    model.setup_materials_from_db(materials) 
    model.lb = torch.tensor(processor.bounds['lb'], dtype=torch.float32).to(DEVICE)
    model.ub = torch.tensor(processor.bounds['ub'], dtype=torch.float32).to(DEVICE)
    model.weld_duration = float(processor.bounds['ub'][3])

    # ==========================================
    # 3. 执行训练循环 (纯 CPU/GPU 计算，无异步问题)
    # ==========================================
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(model.opt, T_0=5000)
    scaler = GradScaler()
    bs = 6000
    n_hard_samples = 500
    hard_idx = torch.randint(0, len(X_train), (n_hard_samples,), device=DEVICE)

    for ep in range(epochs + 1):
        model.net_temp.train()
        model.net_disp.train()
        
        # RAR 自适应重采样
        if ep > 0 and ep % 500 == 0:
            model.net_temp.eval()
            pool_idx = torch.randint(0, len(X_train), (20000,), device=DEVICE)
            with torch.no_grad():
                pde_res_pool = model.compute_loss(X_train[pool_idx], Y_train[pool_idx], return_pde_res_only=True)
                pde_res_pool = torch.nan_to_num(pde_res_pool, nan=0.0)
                _, top_indices = torch.topk(pde_res_pool.flatten(), n_hard_samples)
                hard_idx = pool_idx[top_indices]
            model.net_temp.train()

        rand_idx = torch.randint(0, len(X_train), (bs - n_hard_samples,), device=DEVICE)
        idx = torch.cat([rand_idx, hard_idx], dim=0)
        
        model.opt.zero_grad()
        l_pde, l_dT, l_dU = model.compute_loss(X_train[idx], Y_train[idx])
        l_bc = model.compute_bc_loss()
        
        if ep < 2000: w_pde, w_data = 0.0, 100.0 
        elif ep < 10000:
            progress = (ep - 2000) / 8000.0
            w_pde, w_data = 10.0 * progress, 100.0 - 90.0 * progress
        else: w_pde, w_data = 0.1, 100.0 
        
        loss = w_pde * l_pde + w_data * (l_dT + l_dU) + 10.0 * l_bc
        
        scaler.scale(loss).backward()
        scaler.unscale_(model.opt)
        torch.nn.utils.clip_grad_norm_(model.net_temp.parameters(), max_norm=1.0)
        torch.nn.utils.clip_grad_norm_(model.net_disp.parameters(), max_norm=1.0)
        scaler.step(model.opt)
        scaler.update()
        scheduler.step()
        
        if ep % 500 == 0:
            print(f"[Train] Ep {ep}/{epochs} Loss: {loss.item():.4f}")

    # ==========================================
    # 4. 执行验证，计算核心指标
    # ==========================================
    max_def_rel_error = 0.0
    val_metrics = {}
    if val_files:
        print("[*] 开始验证集评估...")
        X_val, Y_val, _ = processor.process_files(val_files, is_training=False)
        T_pred, U_pred = model.predict(X_val)
        
        U_p = U_pred.numpy()
        U_t = Y_val[:,1:4].cpu().numpy()
        
        mag_t = np.sqrt(np.sum(U_t**2, axis=1))
        mag_p = np.sqrt(np.sum(U_p**2, axis=1))
        max_def_t = np.max(mag_t)
        max_def_p = np.max(mag_p)
        
        if max_def_t > 1e-6:
            max_def_rel_error = float(np.abs(max_def_p - max_def_t) / max_def_t * 100.0)
            
        val_metrics = {
            "rmse_t": float(np.sqrt(np.mean((T_pred.numpy().flatten() - Y_val[:,0].cpu().numpy())**2))),
            "rmse_u": float(np.sqrt(np.mean((U_p - U_t)**2))),
            "max_def_t": float(max_def_t),
            "max_def_p": float(max_def_p)
        }

    # ==========================================
    # 5. 保存物理模型，生成相对路径
    # ==========================================
    relative_dir = os.path.join("trained_weights", f"joint_{joint_id}_method_{method_id}")
    filename = f"model_{model_version}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
    relative_path = os.path.join(relative_dir, filename).replace("\\", "/")
    
    absolute_dir = os.path.join(DATA_ROOT, relative_dir)
    os.makedirs(absolute_dir, exist_ok=True)
    
    torch.save({
        'nt': model.net_temp.state_dict(), 
        'nd': model.net_disp.state_dict(), 
        'lb': model.lb, 
        'ub': model.ub
    }, os.path.join(absolute_dir, filename))

    # ==========================================
    # 6. 将模型注册回数据库表 (同步操作)
    # 【修改点3】：去掉 await
    # ==========================================
    TrainedModel.create(
        model_name=f"Auto_PINN_J{joint_id}_M{method_id}",
        version=model_version,
        model_path=relative_path,
        joint_id=joint_id,
        method_id=method_id,
        trained_material_ids=material_ids,
        max_def_rel_error=max_def_rel_error,
        description=description,
        metrics=val_metrics,
        is_deployed=False 
    )
    print(f"[OK] 后台训练任务完成！已成功注册权重文件至 {relative_path}")