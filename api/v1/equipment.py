from fastapi import APIRouter, Depends
from typing import Any
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from schemas.request import equipment_schema
from common.session import get_db
from models.equipment import EquipmentParam


router = APIRouter()


@router.post("/equipment/add", summary="添加激光焊接设备", name="新增一条设备信息")
async def add_material_info(
        req: equipment_schema.EquipmentParamBase
) -> Any:
    try:
        equipment_dict = dict(req)
        result = await EquipmentParam.add_equipment(equipment_dict)
        return resp.ok(data=result, msg=f"设备 '{req.equipment_id}' 添加成功")
        
    except IntegrityError as e:
        error_detail = str(e)
        
        if "unique" in error_detail.lower() or "duplicate" in error_detail.lower():
            error_msg = f"设备编码 '{req.equipment_id}' 已存在"
        else:
            error_msg = "数据完整性错误"
            
        return resp.fail(resp.DataStoreFail.set_msg(error_msg))
    
    except ValueError as ve:
        return resp.fail(resp.InvalidParams.set_msg(str(ve)))
    
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg("系统内部错误"))


@router.delete("/equipment/delete", summary="删除激光焊接设备", name="删除激光焊接设备", dependencies=[Depends(get_db)])
async def del_equipment(
    equipment_id : str
) -> Any:
    try:
        result = await EquipmentParam.del_by_equipment_id(equipment_id = equipment_id)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)


@router.put("/equipment/edit", summary="编辑激光焊接设备", name="编辑激光焊接设备")
async def edit_equipment(
    equipment: equipment_schema.EquipmentParamUpdate,
) -> Any:
    equipment_dict = dict(equipment)

    try:    
        result = await EquipmentParam.update_equipment(equipment_dict)
    except ValueError as e:
        # 处理material_id不存在的情况
        return resp.fail(resp.DataNotFound.set_msg(str(e)))
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('装备编码冲突！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
    return resp.ok(data=result)


@router.get("/equipment/showall",summary='查询所有激光焊接设备',name='查询所有激光焊接设备')
async def get_all_equipments() -> Any:
    """获取所有设备"""
    try:
        result = await EquipmentParam.select_all()
        return resp.ok(data=result)
    except Exception as e:
        print(f"查询所有设备失败: {e}")
        return resp.fail(resp.DataNotFound, detail=str(e))


@router.post("/equipment/search", summary="条件筛选激光焊接设备", name="按条件筛选激光焊接设备信息")
async def search_equipment(
    filter_params: equipment_schema.EquipmentFilter,
    page: int = 1,
    page_size: int = 20
) -> Any:
    """
    根据条件筛选激光焊接设备信息
    
    - **filter_params**: 筛选条件
    - **page**: 页码,从1开始
    - **page_size**: 每页数量
    """
    try:
        # 转换为字典并移除None值
        filter_dict = filter_params.dict(exclude_none=True)
        
        # 执行筛选
        result = await EquipmentParam.search_equipment(
            filter_params=filter_dict,
            page=page,
            page_size=page_size
        )
        
        return resp.ok(data=result)
        
    except Exception as e:
        print(f"筛选设备失败: {e}")
        return resp.fail(resp.DataQueryFail.set_msg(f"数据查询失败: {str(e)}"))