import pytz

from utils.tools_func import tz
from models.w_pred_model import TrainedModel
from schemas.request import sys_w_pred_model_schema
from common import deps, logger
from common.session import db, async_db
from fastapi import APIRouter, Depends, HTTPException, Form, status,Path
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
import datetime
import os

router = APIRouter()
DATA_ROOT = r"E:\welding_data"  # 请替换为你的实际根目录

# ==========================================
# 1. 增: 注册新模型
# ==========================================
@router.post("/model_registry/add", summary="注册新接头通用模型")
async def add_trained_model(req: sys_w_pred_model_schema.TrainedModelCreate):
    try:
        data = req.dict()
        
        # 【排他逻辑】同一个接头+同一种方法，只能有一个激活模型
        if data.get('is_deployed'):
            await TrainedModel.update(is_deployed=False).where(
                (TrainedModel.joint_id == data['joint_id']) &
                (TrainedModel.method_id == data['method_id'])
            ).execute()

        new_model = await async_db.create(TrainedModel, **data)
        return {"code": 200, "data": {"id": new_model.id}, "msg": "模型注册成功"}
    except Exception as e:
        return {"code": 500, "msg": f"模型注册失败: {str(e)}"}

# ==========================================
# 2. 查: 获取模型列表
# ==========================================
@router.get("/model_registry/search", summary="查询通用模型列表")
async def search_trained_models(query: sys_w_pred_model_schema.TrainedModelQuery = Depends()):
    try:
        sql_query = TrainedModel.select()
        filters = []
        if query.joint_id: filters.append(TrainedModel.joint_id == query.joint_id)
        if query.method_id: filters.append(TrainedModel.method_id == query.method_id)
        if query.is_deployed is not None: filters.append(TrainedModel.is_deployed == query.is_deployed)
            
        if filters: sql_query = sql_query.where(*filters)
        
        # 激活的排最上面，然后按变形误差从小到大
        sql_query = sql_query.order_by(
            TrainedModel.is_deployed.desc(),       
            TrainedModel.max_def_rel_error.asc()   
        )
        
        total = await async_db.count(sql_query)
        results = await async_db.execute(sql_query.paginate(query.current_page, query.page_size))
        
        data_list = [r.__data__ for r in results]
        return {"code": 200, "data": {"list": data_list, "total": total}}
    except Exception as e:
        return {"code": 500, "msg": f"查询异常: {str(e)}"}

# ==========================================
# 3. 改: 更新模型信息 (包含切换上线状态)
# ==========================================
@router.put("/model_registry/{model_id}", summary="修改模型信息")
async def update_trained_model(
    model_id: int = Path(..., gt=0),
    req: sys_w_pred_model_schema.TrainedModelUpdate = None
):
    try:
        obj = await async_db.get(TrainedModel, id=model_id)
        update_data = req.dict(exclude_unset=True)
        
        # 【排他逻辑】如果将该模型设为上线
        if update_data.get("is_deployed") is True:
            await TrainedModel.update(is_deployed=False).where(
                (TrainedModel.joint_id == obj.joint_id) &
                (TrainedModel.method_id == obj.method_id) &
                (TrainedModel.id != model_id)
            ).execute()
        
        # 更新时间戳
        update_data['updated_at'] = datetime.datetime.now()
        
        for key, value in update_data.items():
            setattr(obj, key, value)
        await async_db.update(obj)
        
        return {"code": 200, "msg": "模型信息更新成功"}
    except Exception as e:
        return {"code": 500, "msg": f"更新失败: {str(e)}"}

# ==========================================
# 4. 删: 删除模型记录
# ==========================================
@router.delete("/model_registry/{model_id}", summary="删除模型权重记录")
async def delete_trained_model(
    model_id: int = Path(..., gt=0), 
    delete_file: bool = False
):
    try:
        obj = await async_db.get(TrainedModel, id=model_id)
        
        if obj.is_deployed:
            return {"code": 403, "msg": "该模型正在线上服务，禁止删除。请先切换至其他模型。"}
        
        file_to_delete = os.path.join(DATA_ROOT, obj.model_path) if obj.model_path else None
        
        await async_db.delete(obj)
        
        file_msg = "保留了物理文件"
        if delete_file and file_to_delete and os.path.exists(file_to_delete):
            try:
                os.remove(file_to_delete)
                file_msg = "并清理了服务器上的 .pth 文件"
            except Exception as fe:
                file_msg = f"物理文件清理失败: {fe}"
                
        return {"code": 200, "msg": f"记录删除成功，{file_msg}"}
    except Exception as e:
        return {"code": 500, "msg": f"删除失败: {str(e)}"}