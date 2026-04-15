from models.material import Material
from fastapi import APIRouter, Depends
from typing import Any
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from schemas.request import material_schema
from common.session import get_db

router = APIRouter()


@router.post("/material/add", summary="添加母材", name="新增一条母材信息")
async def add_material_info(req: material_schema.MaterialBase) -> Any:
    try:
        material_data = req.dict()
        new_id = await Material.add_material(material_data)
        return resp.ok(data={"id": new_id}, msg=f"材料 '{req.name}' 添加成功")
        
    except IntegrityError as e:
        error_detail = str(e)
        if "duplicate" in error_detail.lower():
            error_msg = f"材料名称 '{req.name}' 已存在，请勿重复录入"
        else:
            error_msg = "数据库完整性错误"
        return resp.fail(resp.DataStoreFail.set_msg(error_msg))
    
    except Exception as e:
        # 记录日志并返回通用错误
        print(f"系统异常: {e}")
        return resp.fail(resp.DataStoreFail.set_msg("系统内部错误"))