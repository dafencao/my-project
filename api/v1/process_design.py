from models.process_design import ProcessDesign
from fastapi import APIRouter, Depends
from typing import Any
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
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
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('工艺编码已存在！'))
    
    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))
    
    return resp.ok(data=result)


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


@router.get("/process/showall",summary='查询所有工艺',name='查询所有工艺')
async def get_all_processs() -> Any:
    """获取所有工艺"""
    try:
        result = await ProcessDesign.select_all()
        return resp.ok(data=result)
    except Exception as e:
        print(f"查询所有工艺失败: {e}")
        return resp.fail(resp.DataNotFound, detail=str(e))