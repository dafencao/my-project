from models.material import MaterialInfo
from common import deps, logger
from common.session import db, async_db
from core import security
from fastapi import APIRouter, Depends, HTTPException, Form,HTTPException, status
from datetime import datetime, timedelta
from typing import Any,List
from schemas.response import resp
from schemas.request import sys_userrole_schema
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
import asyncio
from schemas.request import material_schema

router = APIRouter()


@router.post("/material/add", summary="添加母材", name="新增一条母材信息")
async def add_material_info(
        req: material_schema.MatericalBase
) -> Any:
    try:
        material = dict(req)
        result =await MaterialInfo.add_material(material)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('材料编码已存在！'))

    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))

    return resp.ok(data=result)