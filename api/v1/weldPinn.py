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
from models.material import Material
from models.weldPinn import ModelManager
from common import deps, logger
from common.session import db, async_db
from core import security
from fastapi import APIRouter, Depends, HTTPException, Form, status
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
        # 1. 动态选型：寻找匹配接头和方法的“已锁定（验证通过）”的训练记录
        record = await WProcessRecord.select().where(
            (WProcessRecord.joint_id == req.joint_id) & 
            (WProcessRecord.method_id == req.method_id) &
            (WProcessRecord.is_locked == True) &
            (WProcessRecord.model_path.is_null(False))
        ).order_by(WProcessRecord.id.desc()).first()

        if not record:
            return {"code": 404, "msg": "未找到匹配该接头和工艺的预训练模型权重。"}

        # 2. 获取材料参数
        material = await Material.get_or_none(id=req.material_id)
        if not material:
            return {"code": 404, "msg": "材料ID不存在。"}

        # 3. 组装绝对路径并获取引擎
        model_abs_path = os.path.join(DATA_ROOT, record.model_path)
        if not os.path.exists(model_abs_path):
            return {"code": 500, "msg": "数据库记录的模型文件在服务器硬盘上丢失。"}
            
        engine = ModelManager.get_engine(model_abs_path)
        
        # 4. 注入材料参数 (让模型临时适配当前选择的母材)
        engine.setup_material(material.properties) 

        # 5. 动态构建空间网格
        # 从模型的 lb 和 ub 获取当前模型适用的空间边界
        lb = engine.pinn.lb.cpu().numpy()
        ub = engine.pinn.ub.cpu().numpy()
        
        x_val = np.linspace(lb[0], ub[0], req.nx)
        z_val = np.linspace(lb[2], ub[2], req.nz)
        # 这里假设顶面是 3.0，底面是 3.0-Depth (与你的原始代码逻辑一致)
        y_val = np.linspace(3.0 - req.depth, 3.0, req.ny) 
        
        X, Y, Z = np.meshgrid(x_val, y_val, z_val)
        grid_pts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

        # 6. 执行多时刻预测
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
            
            # 返回时顺便附上当前时刻的网格维度，方便前端 Three.js 重建网格
            results.append({
                "time": t,
                "grid_shape": [req.nx, req.ny, req.nz],
                "data": cloud_data
            })

        return {"code": 200, "data": results, "msg": "云图预测成功"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"code": 500, "msg": f"预测引擎异常: {str(e)}"}
