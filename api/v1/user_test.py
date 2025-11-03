from typing import Any, List, Optional
from datetime import datetime, timedelta

import peewee
import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, Header

from core import security
from models import user_test

from models.user_test import UserTest
from models.user_test import TestPost

from common import deps, logger
from models.usermenu import Usermenu
from models.userrole import RoleMenuRelp, Userrole
from schemas.response import resp
from schemas.request import sys_user_test_schema
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from logic.user_logic import UserInfoLogic
from schemas.request import sys_user_schema
from common.session import db, get_db
from datetime import datetime
from utils.tools_func import rolePremission, tz

router = APIRouter()
@router.post("/add", summary="新增一条用户记录", name="添加用户")
async def add_use_test(
        user_test: sys_user_test_schema.UserTestBase
)-> Any:
    user_test = user_test.dict()
    try:
        async with db.atomic_async():

            result = await UserTest.add_user(user_test)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('用户已存在，芜湖'))

    except Exception as e:
        return  resp.fail(resp.DataStoreFail,detail=str(e))
    return resp.ok(data=result)



@router.post("/addpost", summary="新增部门", name="添加部门")
async def add_testpost(
        testpost: sys_user_test_schema.TestPostAdd
)-> Any:
    testpost = testpost.dict()

    result = await TestPost.add_post(testpost)
    return resp.ok(data=result)




@router.delete("/delete", summary="删除一条用户信息", name="删除用户")
async def del_user_test(
        id: str
) -> Any:

    result = await UserTest.del_by_user_testid(id)
    if result == 0:
         res= resp.fail(resp.DataDestroyFail.set_msg('7.7删除失败'))
         print('res')
         print(res)
         print(type(res))
         return res
    if result >1:
        return resp.ok(data=result)
    # return result





@router.put("/update", summary="修改一条用户记录", name="编辑用户")
async def edit_user_test(
        # userinfo: dict  修改与添加大同小异 修改没有password字段
        user_test: sys_user_test_schema.UserTestUpdate,
) -> Any:
    user_test = user_test.dict()

    user_test = dict_to_model(UserTest, user_test)

    if True:
        async with db.atomic_async():
            result = await UserTest.update_user_test(user_test)

    return result


@router.post("/detail", summary="根据id查看用户信息", name="获取用户信息")
async def query_user_test_id(id: int):
    result =await UserTest.select_by_user_test_id(id)
    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="User not found")


@router.post("/like", summary="模糊查询用户信息", name="获取用户信息")
async def query_user_test_putin(putin:str):
    result =await UserTest.select_by_user_test_putin(putin)

    # print(result)
    return result
    # else:
    #     raise HTTPException(
    #         status_code=404, detail="User not found")

@router.post("/groupID", summary="获取部门、人员", name="获取部门、人员",
             dependencies=[Depends(get_db)])

async def get_UserTest() -> Any:

    db = await UserTest.select_all()

    if db:
        result = list(db)
    else:
        result = []
    return resp.ok(data=result)
