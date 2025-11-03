import string
from typing import Any, List, Optional
from datetime import datetime, timedelta

import peewee
import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, Header

from core import security
from models import user_test
from models.intro_control import IntroControl

from models.user_test import UserTest
from models.user_test import TestPost

from common import deps, logger
from models.usermenu import Usermenu
from models.userrole import RoleMenuRelp, Userrole
from schemas.response import resp
from schemas.request import sys_user_test_schema, sys_intro_control_schema
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from logic.user_logic import UserInfoLogic
from schemas.request import sys_user_schema
from common.session import db, get_db, async_db
from datetime import datetime
from utils.tools_func import rolePremission, tz, convert_num_arr, convert_arr
from models.intro_control import IntroControl
from models.fan import FanApplicationModel
from  models.fan_introduction import Fan_introduction


router = APIRouter()


# 机车接口
@router.post("/intro/add", summary="新增一条产品位置信息", name="产品位置信息")
async def add_intro_control(
         intro_control: sys_intro_control_schema.IntroBase
)-> Any:
    intro_control = dict(intro_control)
    # id = intro_control_show[0]
    # intro_control = intro_control_show[1]
    # show = intro_control['id']
    # updatefan = {"show":show}
    # result1 = await Fan_introduction.update_fan(id, updatefan)
    # print(intro_control)
    intro_control['imagePosition'] = ",".join(str(i) for i in intro_control['imagePosition'])
    intro_control['circle'] = ",".join(list(map(str, intro_control['circle'])))
    intro_control['text'] = ",".join(list(map(str, intro_control['text'])))
    intro_control['circleNode'] = ",".join(list(map(str, intro_control['circleNode'])))
    intro_control['linePoints'] = ",".join(list(map(str, intro_control['linePoints'])))
    res = await async_db.execute(
            FanApplicationModel.select(FanApplicationModel.code).dicts())
    res = list(res)
    # co_list = []
    code_list = []
    for item in res:
        code = item.get('code')
        code = int(code)
        code_list.append(code)
    # for st in code_list:
    #     code = int(st)
    #     code_list.append(code)
    # id_list = [d["id"] for d in id_list]
    print(code_list)

    if not intro_control['trainType'] in code_list:
        return resp.fail(resp.DataStoreFail.set_msg('该车型不存在！'))
    elif intro_control['trainType'] in code_list:
        try:
            # if IntroControl.trainType == Fan_introduction.id:
            async with db.atomic_async():
                result = await IntroControl.add_intro(intro_control)
                # print(result)
                # # show = intro_control['id']
                # updatefan = {"show": result}
                # result1 = await Fan_introduction.update_fan(id, updatefan)
        except IntegrityError as e:
            return resp.fail(resp.DataStoreFail.set_msg('数据已存在'))
        except Exception as e:
            return resp.fail(resp.DataStoreFail,detail=str(e))
        return resp.ok(data=result)
    # else:
    #     try:
    #         async with db.atomic_async():
    #
    #             result = None
    #     except IntegrityError as e:
    #             return resp.fail(resp.DataStoreFail.set_msg('车型不存在'))
    #     return resp.ok(data=result)


@router.delete("/intro/delete", summary="删除一条产品数据", name="删除产品管理数据")
async def del_intro_control(
        id: str
) -> Any:
    intro_controlid = id
    # intro_control= await IntroControl.select_by_intro_control_id(id)
    # intro_control= intro_control[0]
    # # show = db1['id']
    # print(intro_control)
    # db2 = await async_db.execute(Fan_introduction.select().where(Fan_introduction.show == id).dicts())
    # db2 = list(db2)
    # id = db2[0]['id']
    # updatefan = {"show": None }
    # print(updatefan)
    # result1 = await Fan_introduction.update_fan(id, updatefan)
    result = await IntroControl.del_by_intro_controlid(intro_controlid)
    return resp.ok(data=result)

@router.put("/intro/update", summary="更新一条产品介绍数据", name="编辑产品介绍数据")
async def edit_intro_control(
        intro_control_list: List[sys_intro_control_schema.IntroUpdate],
) -> Any:
    id_list = await async_db.execute(
        FanApplicationModel.select(FanApplicationModel.id).dicts())
    id_list = list(id_list)
    # print(id_list)
    id_list = [d["id"] for d in id_list]
    code_list = []
    for code in id_list:
        code_list.append(int(code))
    # print(code_list)
    # trainType = []
    result = []
    for train in intro_control_list:
        train = train.dict()
        # print(train)
        # global code_list
        if train['trainType'] in code_list:
            # async with async_db.atomic():
            # print(train['trainType'])
            train['imagePosition'] = ",".join(list(map(str, train['imagePosition'])))
            train['circle'] = ",".join(list(map(str, train['circle'])))
            train['text'] = ",".join(list(map(str, train['text'])))
            train['circleNode'] = ",".join(list(map(str, train['circleNode'])))
            train['linePoints'] = ",".join(list(map(str, train['linePoints'])))
            # print(train)
            # train['imagePosition'] = ",".join(train['imagePosition'])
            intro_control = dict_to_model(IntroControl, train)
            #     async with db.atomic_async():
            result1 = await IntroControl.update_intro_control(intro_control)
            if result1:
                result.append("图片"+train['id']+"更新成功")
            else:
                result.append("图片"+train['id']+"更新失败")
        else:
            return resp.fail(resp.DataUpdateFail.set_msg('该车型不存在！'))
    return resp.ok(data=result)

@router.post("/intro/detail", summary="根据id查看产品介绍数据", name="获取产品介绍数据")
async def query_intro_control_id(id: str):
    result =await IntroControl.select_by_intro_control_id(id)
    print(result)

    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="Data not found")
@router.post("/intro/show", summary="查看产品介绍数据", name="获取所有产品介绍数据")
async def query_intro_control():
    result =await IntroControl.select_intro_control()
    # print(result)
    # print(result[4]['imagePosition'][2])
    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="Data not found")
# #动车接口
# @router.post("/bullet/add", summary="新增一条动车位置信息", name="动车位置信息")
# async def add_bullet_control(
#         bullet_control: sys_intro_control_schema.BulletBase
# )-> Any:
#
#     bullet_control = bullet_control.dict()
#     bullet_control['imagePosition'] = ",".join(list(map(str, bullet_control['imagePosition'])))
#     bullet_control['circle'] = ",".join(list(map(str, bullet_control['circle'])))
#     bullet_control['text'] = ",".join(list(map(str, bullet_control['text'])))
#     bullet_control['circleNode'] = ",".join(list(map(str, bullet_control['circleNode'])))
#     bullet_control['linePoint'] = ",".join(list(map(str, bullet_control['linePoint'])))
#
#
#
#     try:
#         async with db.atomic_async():
#
#             result = await BulletControl.add_bullet(bullet_control)
#     except IntegrityError as e:
#         return resp.fail(resp.DataStoreFail.set_msg('数据已存在'))
#
#     except Exception as e:
#         return  resp.fail(resp.DataStoreFail,detail=str(e))
#     return resp.ok(data=result)
#
# @router.delete("/bullet/delete", summary="删除一条动车数据", name="删除动车数据")
# async def del_bullet_control(
#         id: str
# ) -> Any:
#
#     result = await BulletControl.del_by_bullet_controlid(id)
#     if result == 0:
#          res= resp.fail(resp.DataDestroyFail.set_msg('7.7删除失败'))
#          print('res')
#          print(res)
#          print(type(res))
#          return res
#     if result >1:
#         return resp.ok(data=result)
#
#
# @router.put("/bullet/update", summary="修改一条动车记录", name="编辑动车数据")
# async def edit_bullet_control(
#         # userinfo: dict  修改与添加大同小异 修改没有password字段
#         bullet_control: sys_intro_control_schema.BulletUpdate,
# ) -> Any:
#     bullet_control = bullet_control.dict()
#
#     bullet_control = dict_to_model(BulletControl, bullet_control)
#
#     if True:
#         async with db.atomic_async():
#             result = await BulletControl.update_bullet_control(bullet_control)
#
#     return result
#
# @router.post("/bullet/detail", summary="根据id查看动车数据", name="获取动车数据")
# async def query_bullet_control_id(id: int):
#     result =await BulletControl.select_by_bullet_control_id(id)
#
#     if result:
#         return resp.ok(data=result)
#     else:
#         raise HTTPException(
#             status_code=404, detail="Data not found")