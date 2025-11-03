from typing import Any

from pydantic import json

from models.userrole import RoleMenuRelp, Userrole
from schemas.response import resp
from schemas.request import sys_userinfo_schema
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from logic.user_logic import UserInfoLogic
from schemas.request import sys_user_schema
from common.session import db, get_db
from datetime import datetime
from utils.tools_func import rolePremission, tz
from fastapi import APIRouter, Depends, HTTPException, Form, Header
from models.linedeep import LineMethod

router = APIRouter()


@router.post("/lineDeep", summary="熔深测量", name="熔深测量")
async def line_deep(param: Any):

    print(param)
    result = await LineMethod.line_deep_measure(param)
    return resp.ok(data=result)