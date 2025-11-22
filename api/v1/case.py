from models.case import CaseQuality
from fastapi import APIRouter, Depends
from typing import Any
from schemas.response import resp
from peewee import fn, IntegrityError
from schemas.request import case_schema
from common.session import get_db


router = APIRouter()


@router.post("/caseQuality/add", summary="添加焊接案例和焊接质量检测记录", name="新增焊接案例和焊接质量检测记录")
async def add_caseQuality_info(
        req: case_schema.CaseQualityBase
) -> Any:
    try:
        case_quality = dict(req)
        result = await CaseQuality.add_caseQuality(case_quality)
        return resp.ok(data=result, msg=f"案例 '{req.case_id}' 添加成功")
        
    except IntegrityError as e:
        error_detail = str(e)
        
        if "unique" in error_detail.lower() or "duplicate" in error_detail.lower():
            error_msg = f"案例编码 '{req.case_id}' 已存在"
        elif "foreign" in error_detail.lower():
            if "process" in error_detail.lower():
                error_msg = f"关联工艺ID '{req.related_process_id}' 不存在"
            else:
                error_msg = "关联数据不存在"
        else:
            error_msg = "数据完整性错误"
            
        return resp.fail(resp.DataStoreFail.set_msg(error_msg))
    
    except ValueError as ve:
        return resp.fail(resp.InvalidParams.set_msg(str(ve)))
    
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg("系统内部错误"))


@router.delete("/case/delete", summary="删除焊接案例和焊接质量检测记录", name="删除焊接案例和焊接质量检测记录", dependencies=[Depends(get_db)])
async def del_process(
    caseQuality_id : str
) -> Any:
    try:
        result = await CaseQuality.del_by_caseQuality_id(caseQuality_id = caseQuality_id)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)


@router.put("/case/edit", summary="编辑焊接案例和焊接质量检测记录", name="编辑焊接案例和焊接质量检测记录")
async def edit_process(
    case: case_schema.CaseQualityUpdate,
) -> Any:
    case_dict = dict(case)

    try:    
        result = await CaseQuality.update_case_quality(case_dict)
    except ValueError as e:
        # 处理material_id不存在的情况
        return resp.fail(resp.DataNotFound.set_msg(str(e)))
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('案例编码冲突！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
    return resp.ok(data=result)


@router.get("/case/showall",summary='查询所有焊接案例和焊接质量检测记录',name='查询所有焊接案例和焊接质量检测记录')
async def get_all_caseQualitys(
    page: int = 1,
    page_size: int = 20, 
) -> Any:
    """获取所有工艺（分页）"""
    try:
        result = await CaseQuality.select_all(page=page, page_size=page_size)
        return resp.ok(data=result)
    except Exception as e:
        print(f"查询所有工艺失败: {e}")
        return resp.fail(resp.DataNotFound, detail=str(e))


@router.post("/case/search", summary="条件焊接案例和焊接质量检测记录", name="按条件焊接案例和焊接质量检测记录")
async def search_process(
    filter_params: case_schema.CaseQualityFilter,
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
        result = await CaseQuality.select_with_filter(
            filter_params=filter_params,
            page=page,
            page_size=page_size
        )
        
        return resp.ok(data=result)
        
    except Exception as e:
        print(f"筛选工艺失败: {e}")
        return resp.fail(resp.DataQueryFail.set_msg(f"数据查询失败: {str(e)}"))