from models.material import Material
from fastapi import APIRouter, Path, Depends
from typing import Any
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from schemas.request import material_schema
from common.session import get_db

router = APIRouter()


# --- 1. 新增接口 (纯插入) ---
@router.post("/material/add", summary="添加母材", name="新增一条母材信息")
async def add_material_info(req: material_schema.MaterialCreate) -> Any:
    try:
        success, new_id, msg = await Material.add_material(req.dict())
        if success:
            return resp.ok(data={"id": new_id}, msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg)) # 处理重名错误
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 2. 更新接口 (基于ID) ---
@router.put("/material/{material_id}", summary="修改母材", name="更新现有母材信息")
async def update_material_info(
    material_id: int = Path(..., description="材料数据库主键ID"),
    req: material_schema.MaterialUpdate = None
) -> Any:
    try:
        # exclude_unset=True 极其重要：前端没传的字段不会变成 None
        update_data = req.dict(exclude_unset=True) 
        if not update_data:
            return resp.fail(resp.DataStoreFail.set_msg("没有任何需要更新的数据"))

        success, msg = await Material.update_material(material_id, update_data)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 3. 删除接口 ---
@router.delete("/material/{material_id}", summary="删除母材", name="根据ID删除材料")
async def delete_material_info(
    material_id: int = Path(..., description="材料数据库主键ID")
) -> Any:
    try:
        success, msg = await Material.delete_material(material_id)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 4. 分页查询接口 ---
@router.get("/material/search", summary="获取母材列表", name="分页查询及条件筛选")
async def search_materials(
    query: material_schema.MaterialQuery = Depends() 
) -> Any:
    try:
        results, total = await Material.filter_materials_with_pagination(
            name=query.name, 
            software=query.source_software,
            page=query.current,
            page_size=query.pageSize
        )
        
        # 组装返回给前端表格的数据结构
        data = {
            "list": [m.__data__ for m in results], 
            "total": total,
            "current": query.current,
            "pageSize": query.pageSize
        }
        return resp.ok(data=data)
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"查询异常: {str(e)}"))