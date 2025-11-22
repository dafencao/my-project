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

    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))
    
    return resp.ok(data=result)


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
