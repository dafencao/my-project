import pytz

from utils.tools_func import tz

'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-04-19 14:48:02
'''

from models.Wdata_manage import WProcessRecord
from models.weld_train_work import background_train_task
from models.material import Material
from models.w_pred_model import TrainedModel
from models.weldPinn import ModelManager
from common import deps, logger
from common.session import db, async_db
from core import security
from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime, timedelta
from typing import Any,List
from schemas.response import resp
from schemas.request import sys_weldPinn_schema
from models.user import UserRoleRelp, Userinfo
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
import os
import numpy as np


router = APIRouter()
DATA_ROOT = r"E:\welding_data"

@router.post("/predict/contour", summary="批量预测3D云图数据")
async def generate_3d_contour(req: sys_weldPinn_schema.BatchPredictRequest):
    try:
        # ==========================================
        # 1. 【核心修正】去 TrainedModel 表中寻址模型
        # ==========================================
        if req.model_id:
            # 前端明确指定了要用哪个历史模型
            record = await TrainedModel.get_or_none(id=req.model_id)
            if not record:
                return {"code": 404, "msg": f"未找到指定的模型 ID: {req.model_id}"}
        else:
            # 前端没指定，自动寻找该接头和方法下 `is_deployed = True` (已上线) 的通用大模型
            record = await TrainedModel.select().where(
                (TrainedModel.joint_id == req.joint_id) & 
                (TrainedModel.method_id == req.method_id) &
                (TrainedModel.is_deployed == True)
            ).first()
            if not record:
                return {"code": 404, "msg": "未指定模型，且该工况下无默认部署的通用模型。"}

        # ==========================================
        # 2. 获取目标预测材料的物性参数
        # ==========================================
        material = await Material.get_or_none(id=req.material_id)
        if not material:
            return {"code": 404, "msg": "材料ID不存在。"}

        # ==========================================
        # 3. 组装绝对路径并初始化/获取缓存引擎
        # 注意：这里的 record 现在是 TrainedModel 的实例，所以它有 model_path
        # ==========================================
        model_abs_path = os.path.join(DATA_ROOT, record.model_path)
        if not os.path.exists(model_abs_path):
            return {"code": 500, "msg": f"数据库记录的模型文件在硬盘上丢失: {record.model_path}"}
            
        engine = ModelManager.get_engine(model_abs_path)
        
        # 动态注入材料属性
        engine.setup_material(material.properties)

        # ==========================================
        # 4. 生成 3D 空间网格
        # ==========================================
        lb = engine.pinn.lb.cpu().numpy()
        ub = engine.pinn.ub.cpu().numpy()
        
        x_val = np.linspace(lb[0], ub[0], req.nx)
        z_val = np.linspace(lb[2], ub[2], req.nz)
        y_val = np.linspace(3.0 - req.depth, 3.0, req.ny) 
        
        X, Y, Z = np.meshgrid(x_val, y_val, z_val)
        grid_pts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

        # ==========================================
        # 5. 执行多时刻云图预测
        # ==========================================
        results = []
        for t in req.time_points:
            params = {
                "Time": t,
                "Power": req.power,
                "Speed": req.speed,
                "Radius": req.radius,
                "Depth": req.depth
            }
            cloud_data = engine.predict_cloud(grid_pts, params)
            
            results.append({
                "time": t,
                "grid_shape": [req.nx, req.ny, req.nz],
                "data": cloud_data
            })

        return {
            "code": 200, 
            "data": results, 
            "msg": f"预测成功，使用的是通用模型: {record.model_name}"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"code": 500, "msg": f"预测引擎异常: {str(e)}"}
    
@router.post("/train/start", summary="启动后台训练任务")
async def start_training(req: sys_weldPinn_schema.TrainStartRequest, bg_tasks: BackgroundTasks):
    """
    接收前端发起的训练指令。
    将耗时的 PINN 训练过程挂载到 FastAPi 的 BackgroundTasks 中执行，
    接口立即返回成功，避免前端等待超时。
    """
    
    # 把耗时任务丢给后台 worker
    bg_tasks.add_task(
        background_train_task,
        joint_id=req.joint_id,
        method_id=req.method_id,
        model_version=req.version,
        description=req.description,
        epochs=req.epochs
    )
    
    return {
        "code": 200, 
        "msg": "训练任务已成功提交至后台计算节点。请稍后在【模型注册表】中查看训练结果。"
    }
