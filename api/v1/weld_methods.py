from models.weld_methods import WeldingMethod
from fastapi import APIRouter, Path, Depends
from typing import Any
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from schemas.request import sys_weld_methods_schema
from common.session import get_db

router = APIRouter()

# --- 1. 新增 ---
@router.post("/method/add", summary="添加焊接方法", name="录入新的焊接工艺")
async def add_welding_method(req: sys_weld_methods_schema.WeldingMethodCreate) -> Any:
    try:
        # 使用 .dict() 提取数据
        data = req.dict() 
        success, new_id, msg = await WeldingMethod.add_method(data)
        
        if success:
            return resp.ok(data={"id": new_id}, msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 2. 删除 ---
@router.delete("/method/{method_id}", summary="删除焊接方法", name="根据ID删除工艺")
async def delete_welding_method(method_id: int = Path(...)) -> Any:
    try:
        success, msg = await WeldingMethod.delete_method(method_id)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 3. 更新 ---
@router.put("/method/{method_id}", summary="更新焊接方法", name="修改工艺参数")
async def update_welding_method(
    method_id: int = Path(...),
    req: sys_weld_methods_schema.WeldingMethodUpdate = None
) -> Any:
    try:
        # exclude_unset=True 防止未填字段覆盖旧数据
        update_data = req.dict(exclude_unset=True)
        if not update_data:
            return resp.fail(resp.DataStoreFail.set_msg("没有提供任何需要更新的数据"))

        success, msg = await WeldingMethod.update_method(method_id, update_data)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 4. 查询 ---
@router.get("/method/search", summary="搜索焊接方法", name="分页及条件筛选")
async def search_welding_methods(query: sys_weld_methods_schema.WeldingMethodQuery = Depends()) -> Any:
    try:
        results, total = await WeldingMethod.filter_methods(
            code=query.method_code,
            name=query.method_name,
            page=query.current,
            page_size=query.pageSize
        )
        
        data = {
            "list": [m.__data__ for m in results],
            "total": total,
            "current": query.current,
            "pageSize": query.pageSize
        }
        return resp.ok(data=data)
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"查询异常: {str(e)}"))
    
@router.get("/method/list/all", summary="获取所有焊接方法", name="查询全量焊接方法列表")
async def get_all_welding_methods() -> Any:
    """
    不分页获取数据库中所有的焊接方法。
    主要用于前端界面中需要展示焊接方法下拉列表的场景。
    """
    try:
        results = await WeldingMethod.get_all_methods()
        
        # 将 Peewee 查询结果转换为字典列表
        # m.__data__ 包含了模型中定义的所有字段数据
        data = [m.__data__ for m in results]
        
        return resp.ok(data=data, msg="获取焊接方法列表成功")
        
    except Exception as e:
        # 记录异常并返回统一的错误格式
        print(f"查询焊接方法全量列表异常: {str(e)}")
        return resp.fail(resp.DataStoreFail.set_msg(f"查询失败: {str(e)}"))