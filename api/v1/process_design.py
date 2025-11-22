from models.process_design import ProcessDesign
from fastapi import APIRouter, Depends
from typing import Any
from schemas.response import resp
from peewee import fn, IntegrityError
from schemas.request import processDesign_schema
from common.session import get_db

router = APIRouter()


@router.post("/process/add", summary="添加焊接工艺", name="新增焊接工艺")
async def add_material_info(
        req: processDesign_schema.ProcessDesignBase
) -> Any:
    try:
        process = dict(req)
        result = await ProcessDesign.add_process(process)
        return resp.ok(data=result, msg=f"工艺 '{req.process_id}' 添加成功")
        
    except IntegrityError as e:
        error_detail = str(e)
        
        if "unique" in error_detail.lower() or "duplicate" in error_detail.lower():
            error_msg = f"工艺编码 '{req.process_id}' 已存在"
        elif "foreign" in error_detail.lower():
            if "material" in error_detail.lower():
                error_msg = f"关联材料ID '{req.related_material_id}' 不存在"
            elif "equipment" in error_detail.lower():
                error_msg = f"关联设备ID '{req.related_equipment_id}' 不存在"
            else:
                error_msg = "关联数据不存在"
        else:
            error_msg = "数据完整性错误"
            
        return resp.fail(resp.DataStoreFail.set_msg(error_msg))
    
    except ValueError as ve:
        return resp.fail(resp.InvalidParams.set_msg(str(ve)))
    
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg("系统内部错误"))


@router.delete("/process/delete", summary="删除焊接工艺", name="删除焊接工艺", dependencies=[Depends(get_db)])
async def del_process(
    process_id : str
) -> Any:
    try:
        result = await ProcessDesign.del_by_process_id(process_id = process_id)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)


@router.put("/process/edit", summary="编辑焊接工艺", name="编辑焊接工艺")
async def edit_process(
    process: processDesign_schema.ProcessDesignUpdate,
) -> Any:
    process_dict = dict(process)

    try:    
        result = await ProcessDesign.update_process(process_dict)
    except ValueError as e:
        # 处理process_id不存在的情况
        return resp.fail(resp.DataNotFound.set_msg(str(e)))
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('工艺编码冲突！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
    return resp.ok(data=result)


@router.get("/process/showall", summary='查询所有工艺', name='查询所有工艺')
async def get_all_processs(
    page: int = 1,
    page_size: int = 20, 
) -> Any:
    """获取所有工艺（分页）"""
    try:
        result = await ProcessDesign.select_all(page=page, page_size=page_size)
        return resp.ok(data=result)
    except Exception as e:
        print(f"查询所有工艺失败: {e}")
        return resp.fail(resp.DataNotFound, detail=str(e))
    

@router.post("/process/search", summary="条件筛选焊接工艺", name="按条件筛选焊接工艺信息")
async def search_process(
    filter_params: processDesign_schema.ProcessDesignFilter,
    page: int = 1,
    page_size: int = 20
) -> Any:
    """
    根据条件筛选焊接工艺信息
    
    - **filter_params**: 筛选条件
    - **page**: 页码,从1开始
    - **page_size**: 每页数量
    """
    try:
        # 执行筛选
        result = await ProcessDesign.select_with_filter(
            filter_params=filter_params,
            page=page,
            page_size=page_size
        )
        
        return resp.ok(data=result)
        
    except Exception as e:
        print(f"筛选工艺失败: {e}")
        return resp.fail(resp.DataQueryFail.set_msg(f"数据查询失败: {str(e)}"))