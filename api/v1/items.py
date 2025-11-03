'''
Descripttion: 
version: 
Author: congsir
Date: 2023-02-13 14:10:08
LastEditors: Please set LastEditors
LastEditTime: 2023-05-10 11:00:22
'''
import json
import time
import uuid

import requests
from peewee import fn
from playhouse.shortcuts import model_to_dict

# from auth.auth_casbin import Authority, get_casbin
from common.session import get_db, async_db, db
from common.sys_kafka import kafka_client
from models.file_info import FileInfo
from models.update_fan_record import FanUpdateRecord, FanUpdateRecordRelp
from models.user import Department, Userpost, Userline, Level, Userinfo
from models.userrole import Userrole
from schemas.request import sys_user_action
# from schemas.request.sys_casbin import UserPerm
from utils.file import up_file
from utils.tools_func import convert_arr

# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/16 15:21
# @Author  : CoderCharm
# @File    : endpoints.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""

"""

# from common.sys_redis import redis_client

import os
from typing import Any, List
import shutil
from tempfile import NamedTemporaryFile
from pathlib import Path
from fastapi import APIRouter, File, Request, UploadFile, Query, Depends
from common.sys_redis import redis_client
from models.fan import FanApplicationModel, FanCategory, Fan
from schemas.response import resp

import casbin
# from kafka import KafkaConsumer


router = APIRouter()


# @router.get("/test", name="测试接口")
# def items_test(
#         *,
#         bar: str = Query(..., title="测试字段", description="测试字段描述")
# ) -> Any:
#     """
#     用户登录
#     :param bar:
#     :param db:
#     :return:
#     """
#     # 测试redis使用
#     redis_client.set("test_items", bar, ex=60)
#     redis_test = redis_client.get("test_items")

#     return resp.ok(data=redis_test)
@router.post("/MainHandler", summary="test", name="test", )
def test():
    # await time.sleep(1000)
    user = Userinfo()
    try:
        """使用await关键字等待阻塞操作"""
        """单条查询使用object.get()方法将原本的peewee操作包裹起来"""
        row = Userinfo.select(Userinfo.realName).where(Userinfo.id == 7).dicts()
        row = list(row)
        print(row)
        """多条查询"""
        query = Userinfo.select(Userinfo.realName).where(Userinfo.realName.startswith('12'))

        return resp.ok(data={'row': row})

    except Exception as e:
        """当查不到数据的时候会抛出DoesNotExist错误"""
        return resp.fail(resp.DataNotFound, detail=str(e))


@router.post("/TestHandler", summary="test", name="test", )
def test():
    return resp.ok(data={'row': 'test here'})


@router.post("/test", summary="test", name="test", )
async def test():
    e = casbin.Enforcer('D:/psad-backend/casbin/model.conf', "D:/psad-backend/casbin/policy.csv")

    sub = "nick"  # the user that wants to access a resource.
    obj = "data1"  # the resource that is going to be accessed.
    act = "read"  # the operation that the user performs on the resource.

    # 添加
    # e.add_policy("alice", "data1", "read")
    # e.remove_policy("nick", "data1", "read")

    if e.enforce(sub, obj, act):
        # permit alice to read data1casbin_sqlalchemy_adapter
        print("通过")
    else:
        # deny the request, show an error
        print("拒绝")


# @router.post('/test1',
#              summary='权限测试接口',
#              description='权限测试接口',
#              )
# async def test_auth(test: UserPerm):
#     e = await get_casbin()
#     result = await e.has_permission(test.user, test.model, test.act)
#     return resp.ok(data={'result': result})
# @router.post("/add/user/perm",
#              summary="添加用户权限",
#              description="添加用户权限",
#              dependencies=[Depends(Authority('auth,add'))])
# async def add_user_perm(user_info: UserPerm):
#     user = await Userinfo.select_by_id(user_info.user)
#     if not user:
#         return '添加权限的用户不存在，请检查用户名'
#
#     e = await get_casbin()
#     res = await e.add_permission_for_user(user_info.user, user_info.model,
#                                     user_info.act)
#     if res:
#         return '添加用户权限添加成功'
#     else:
#         return '添加用户权限失败，权限已存在'
# FastAPI路由
@router.post("/test/send_message")
async def send_kafka_message(message:str):
    data={}
    data['message'] = message

    message = json.dumps(data,ensure_ascii= False)
    # topic = 'psad-user-action-topic'
    topic = 'flinksql'

    result = kafka_client.send_message(topic, message)
    print('result')
    print(result)
    if result :
        return {"status": "Message sent successfully"}
    else:
        return {"status": "Failed to send message"}

# @router.get("/test/consume_message")
# async def send_kafka_message():
#
#     # kafka_client.init_kafka_consumer(['flinksql'])
#     # result = kafka_client.consume_messages()
#
#     consumer = KafkaConsumer('flinksql', bootstrap_servers='localhost:9092',api_version=(0, 10, 2))
#     print('consumer')
#     print(consumer)
#     for msg in consumer:
#         print(msg.value.decode())
#     result =''
#     print('result')
#     print(result)
#     return resp.ok(data=result)
#     # messages = []
#     # for msg in kafka_client.consume_messages():
#     #     messages.append(msg)
#     # return {"messages": messages}
