'''
Descripttion: 
version: 
Author: congsir
Date: 2023-03-30 16:31:59
LastEditors: 
LastEditTime: 2023-04-26 16:53:19
'''
from datetime import datetime

import pytz
from fastapi import APIRouter, Depends
from playhouse.shortcuts import dict_to_model

from common.session import get_db, async_db

from models.fan import FanApplicationModel
from models.intro_control import IntroControl
from schemas.response import resp
from schemas.request import sys_fan_schema


router = APIRouter()

# 


@router.get("/all", summary="获取所有应用车型", dependencies = [Depends(get_db)])
async def get_application_model():
    result =await FanApplicationModel.select_all()
    data = []
    for item in result:
        data.append(item['name'])
    return resp.ok(data=data)

@router.post("/add", summary="增加应用车型" )
async def add_application_model(req:sys_fan_schema.ApplModelCreate):
    req.updateAt= datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    applModel = dict(req)
    try:
        result =await FanApplicationModel.create(**applModel)
        return resp.ok(data=result)
    except Exception as e:
        return resp.fail(resp.DataStoreFail)

@router.put("/update", summary="更新应用车型" )
async def update_application_model(req:sys_fan_schema.ApplModelUpdate):
    req.updateAt=datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    try:
        applModel = dict_to_model(FanApplicationModel, dict(req))
        # print('applModel')
        # print(applModel)
        # applModel.save()
        await FanApplicationModel.model_update_one(applModel)
        return resp.ok()
    except Exception as e:
        return resp.fail(resp.DataUpdateFail)
@router.delete("/delete", summary="删除应用车型" )
async def update_application_model(id:int):
    res = await async_db.execute(
        IntroControl.select(IntroControl.trainType).dicts())
    res = list(res)
    tp_list = [d["trainType"] for d in res]
    # print(tp_list)
    co = await async_db.execute(
        FanApplicationModel.select(FanApplicationModel.code)
        .where(FanApplicationModel.id == id).dicts())
    co = list(co)
    # int_co = co[0]
    # code = int(int_co)
    print(co)
    code_list = []
    for int_co in co:
        int_co = int_co.get('code')
        # int_co = int(int_co)
        code_list.append(int(int_co))
    code = code_list[0]
    print(code)

    if code in tp_list:
        return resp.fail(resp.DataStoreFail.set_msg('该车型存在数据！'))
    elif not code in tp_list:
        try:
            # FanApplicationModel.delete().where(FanApplicationModel.id==id)
            await FanApplicationModel.delete_by_id(id)
            return resp.ok()
        except Exception as e:
            return resp.fail(resp.DataDestroyFail)