'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-05-08 14:07:01
'''
import pytz

from common import deps
from models.user import Userinfo
from utils.tools_func import tz

'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-04-19 14:48:02
'''

from models.fan_introduction import Fan_introduction
from schemas.response import resp
from schemas.request import sys_fan_introduction_schema
from typing import Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Form
from common.session import db

router = APIRouter()


# 新增


@router.post("/fan_introduction/add", summary="添加风机产品信息", name="新增一条风机产品信息")
async def fan_add(req: sys_fan_introduction_schema.FanCreate,
                  userInfo: Userinfo = Depends(deps.get_current_userinfo),):
    fan = dict(req)
    fan['createAt'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    fan['updateAt'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    fan['createBy'] = userInfo['account']
    fan['updateBy'] = userInfo['account']

    try:
        result = await Fan_introduction.add_fan(fan)
        return resp.ok(data=result)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataStoreFail, detail=str(e))


# 删除


@router.post("/fan_introduction/delete", summary="删除风机产品信息", name="删除风机产品信息")
async def del_fan(req: sys_fan_introduction_schema.FanDelete) -> Any:
    async with db.atomic_async():
        result = await Fan_introduction.del_fan(req.id)
        # await Fan_introduction.delete().where(Fan_introduction.id == result).execute()
    return resp.ok(data=result)
    # return resp.fail(resp.DataDestroyFail, detail=str(e))


# 查找所有


@router.get("/fan_introduction/query_all", summary="查询所有风机产品信息", name="查询所有风机产品信息")
async def query_all() -> Any:
    try:
        data = await Fan_introduction.select_all()
        # print("产品信息", data)
        return resp.ok(data=data)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))


# 根据风机名称及分类查找
@router.post("/fan_introduction/trainType", summary="获取指定车型的介绍", name="获取指定车型的介绍")
async def query_by_trainType(trainType: int):
    try:
        data = await Fan_introduction.select_by_trainType(trainType)
        return resp.ok(data=data)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))


@router.post("/fan_introduction/query_by", summary="任意字段筛选角色记录", name="任意字段筛选角色记录")
async def query_by(query_fan: sys_fan_introduction_schema.FanQuery) -> Any:
    try:
        result = await Fan_introduction.select_by_fan(query_fan)
        # print("输出", result)
        return resp.ok(data=result)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    pass


@router.put("/fan_introduction/update", summary="编辑风机产品信息", name="编辑风机产品信息")
async def update_fan(req: sys_fan_introduction_schema.FanUpdate,userInfo: Userinfo = Depends(deps.get_current_userinfo)) -> Any:
    id = req.id
    updatefan = dict(req)
    updatefan['updateAt'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    updatefan['updateBy'] = userInfo['account']
    updatefan.pop("id")
    result = await Fan_introduction.update_fan(id, updatefan)
    return resp.ok(data=result)
