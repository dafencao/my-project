'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-05-08 08:41:31
'''
import json
import os

import pytz
# from starlette.requests import Request

from common.deps import get_request_info
from common.sys_kafka import kafka_client
from common.sys_redis import redis_client

'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-04-19 14:48:02
'''


# from models.userrole import Userrole

from common.session import db, get_db
from common import deps, logger
from models.user_action import User_action
from fastapi import APIRouter, Header, Depends , Request
from datetime import datetime, timedelta
from typing import Any, Optional
from peewee import fn
from playhouse.shortcuts import model_to_dict, dict_to_model
from schemas.request import sys_user_action
from schemas.response import resp
router = APIRouter()
from common.session import BaseModel, paginator, db, async_db
from models.user import Userinfo

# 新增
#
@router.post("/user_action/add", summary="添加用户行为", name="新增一条用户行为信息" ,dependencies=[Depends(get_db)])
async def user_action_add(req: sys_user_action.UseractionCreate,info: dict = Depends(get_request_info)):
    # print('request')
    # print(request.headers.get('x-real-ip'))
    # print(request )
    # print(request.client)
    # print(request.client.host)

    if info:
        if req.username is None:
            print('前端获取username'+ str(req.username) +'为空！！！！！！！！！！！！！！！！！！！！！！！')
        req.username = info['account']
        # result = redis_client.get(req.username)
        # print('result')
        # print(result)
        print('info')
        print(info)
        req.ip = info['ip']
        req.updateAt = datetime.strftime(
                datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        # ip = request.client.host
        # req.ip = ip
        print('新增一条用户行为信息 req.description')
        print(req.description)
        # print(req)
        params = dict(req)
        db1 = await async_db.execute(Userinfo.select(Userinfo.realName).where(Userinfo.account == info['account']).dicts())
        userRealName1 = list(db1)
        userRealName = userRealName1[0]['realName']
        params['userRealName'] = userRealName
        # print("@@", params)
        params['actionTime'] = datetime.strftime(
            datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        print(params)
        # print(userRealName)
        # print(userRealName)
        # =========向kafka推送消息=========
        topic = os.getenv('KAFKA_TOPIC')
        # topic = 'flinksql'
        need_push_data = {
            "userName": info['account'],
            "userRealName" : userRealName,
            "ip": info['ip'],
            "actionTime": params['actionTime'],
            # "actionModel": req.pageName,
            "actionPage": req.pageArea,
            "actionType": req.actionType,
            "actionName": req.actionName,
            "description": req.description
        }
        message = json.dumps(need_push_data,ensure_ascii= False)
        print('向kafka推送消息 message')
        print(message)
        result = kafka_client.send_message(topic, message)
        if not result:
            return resp.fail(resp.DataStoreFail, detail="Failed to send message")
        # =========向kafka推送消息=========

        try:
            result = await User_action.add_user_action(params)
            return resp.ok(data=result)
        except Exception as e:
            print(e)
            return resp.fail(resp.DataStoreFail,detail=str(e))


# 查找所有
@router.get("/user_action/query_all", summary="查询所有用户行为信息", name="查询所有用户行为信息")
async def query_all(pageSize: int, pageNo: int) -> Any:
    # print("@@@@@@@@@", pageSize, pageNo)
    # try:
    if True:
        data = await User_action.select_all()
        total = len(data)
        # 分页
        current = int(pageNo)
        pageSize = int(pageSize)
        result = data[
            (current*pageSize-pageSize):
            current*pageSize
        ]
        return resp.ok(data=result, total=total)
    # except Exception as e:
    #     print(e)
    #     return resp.fail(resp.DataNotFound )

# # 根据风机名称及分类查找


@router.post("/user_action/query_by", summary="任意字段筛选角色记录", name="任意字段筛选角色记录")
async def query_by(params: sys_user_action.UseractionQuery) -> Any:
    try:
        item_dict = dict(params)
        result =await User_action.select_by(item_dict)
        # print("输出", result)
        total = len(result)
        # 分页
        # current = int(params.pageNo)
        current = int(params.current)
        pageSize = int(params.pageSize)
        result = result[
            (current*pageSize-pageSize):
            current*pageSize
        ]
        return resp.ok(data=result, total=total)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound,detail=str(e))
