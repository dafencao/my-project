from models.material import MaterialInfo
from fastapi import APIRouter, Depends
from typing import Any
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from schemas.request import material_schema
from common.session import get_db

router = APIRouter()


@router.post("/material/add", summary="添加母材", name="新增一条母材信息")
async def add_material_info(
        req: material_schema.MatericalBase
) -> Any:
    try:
        material = dict(req)
        result = await MaterialInfo.add_material(material)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('材料编码已存在！'))

    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))

    return resp.ok(data=result)


@router.delete("/material/delete", summary="删除一个母材", name="删除一个母材", dependencies=[Depends(get_db)])
async def del_material(
    material_id : str
) -> Any:
    try:
        result = await MaterialInfo.del_by_material_id(material_id = material_id)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)


@router.put("/material/edit", summary="编辑已存在母材", name="编辑已存在母材")
async def edit_department(
    material: material_schema.MaterialUpdate,
) -> Any:
    material_dict = dict(material)

    try:    
        result = await MaterialInfo.update_material(material_dict)
    except ValueError as e:
        # 处理material_id不存在的情况
        return resp.fail(resp.DataNotFound.set_msg(str(e)))
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('母材编码冲突！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
    return resp.ok(data=result)


@router.post("/material/search", summary="条件筛选母材", name="按条件筛选母材信息")
async def search_materials(
    filter_params: material_schema.MaterialFilter,
    page: int = 1,
    page_size: int = 20
) -> Any:
    """
    根据条件筛选母材信息
    
    - **filter_params**: 筛选条件
    - **page**: 页码，从1开始
    - **page_size**: 每页数量
    """
    try:
        # 转换为字典并移除None值
        filter_dict = filter_params.dict(exclude_none=True)
        
        # 执行筛选
        result = await MaterialInfo.search_materials(
            filter_params=filter_dict,
            page=page,
            page_size=page_size
        )
        
        return resp.ok(data=result)
        
    except Exception as e:
        print(f"筛选母材失败: {e}")
        # 正确的调用方式
        return resp.fail(resp.DataQueryFail.set_msg(f"数据查询失败: {str(e)}"))
    

@router.get("/material/showall",summary='查询所有母材',name='查询所有母材')
async def get_all_materials() -> Any:
    """获取所有部门"""
    try:
        result = await MaterialInfo.select_all()
        return resp.ok(data=result)
    except Exception as e:
        print(f"查询所有母材失败: {e}")
        return resp.fail(resp.DataNotFound, detail=str(e))