
"""
纯增删改查操作，写在model里面
"""

from datetime import datetime

import pytz

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, ForeignKeyField, TimeField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from schemas.request import sys_user_schema

from peewee import fn, JOIN
import time
from schemas.response import resp
from utils.tools_func import convert_arr, tz


class User_action(BaseModel):

    """
    介绍表 
    """
    id = IntegerField(primary_key=True)  # id
    username = CharField(column_name='username')
    userRealName = CharField(column_name='userRealName')
    actionTime = CharField(column_name='actionTime')
    actionName = CharField(column_name='actionName')
    actionId = CharField(column_name='actionId')
    actionType = CharField(column_name='actionType')
    actionModel = CharField(column_name='actionModel')
    monitorModule = CharField(column_name='monitorModule')
    pageUrl = CharField(column_name='pageUrl')
    pageName = CharField(column_name='pageName')
    pageArea = CharField(column_name='pageArea')
    description = CharField(column_name='description')
    ip = CharField(column_name='ip')

    class Meta:
        table_name = 'user_action'  # 自定义映射的表名

    @classmethod
    def fuzzy_query(cls, queryfan):

        # fn.abs(userinfo.full_pressure - queryUser.full_pressure).alias('count')

        db = User_action.select().order_by(User_action.actionTime.desc()).dicts()

        # .order_by(
        #     # fn.abs(User.flow_rate-queryUser.flowRate),
        # )
        # db = db.offset((queryuserrole.pageNo - 1) *
        #                queryuserrole.pageSize).limit(queryuserrole.pageSize)
        return list(db)


# 新增一条产品信息

    @classmethod
    async def add_user_action(cls, params):  # 添加风机信息

        result = await async_db.create(User_action ,**params)
        return result.id

  # 查询：查询所有信息

    @classmethod
    async def select_all(cls):
        # db = User_action.select(User_action.id, User_action.id).dicts()
        # if username:
        db = await async_db.execute(User_action.select().order_by(User_action.updateAt.desc()).dicts())
        # db = User_action.select().order_by(User_action.actionTime.desc()).dicts()
        # data = db.offset((pageNo - 1) * pageSize).limit(pageSize).dicts()
        if db:
            return list(db)
        else:
            return []

    # 查询：通过用户名称及分类查询信息
    @classmethod
    async def select_by(cls, params):

        # if params
        # print("类型", params)
        # if params.label=="":
        # db = User_action.select().dicts()
        # else:
        # if params.beginTime == '' and params.username == '':
        #     db = User_action.select()
        # elif params.username == '':
        #     db = User_action.select().where(User_action.actionTime > params.beginTime,
        #                                     User_action.actionTime < params.endTime)
        # elif params.beginTime == "":
        #     db = User_action.select().where(User_action.username == params.username)
        # else:
        #     db = User_action.select().where(User_action.actionTime > params.beginTime,
        #                                     User_action.actionTime < params.endTime,
        #                                     User_action.username == params.username)
        if params['updateAt']:
            beginTime = params['updateAt'][0]
            endTime = params['updateAt'][1]
        else:
            beginTime = ''
            endTime = ''
        db =await async_db.execute( User_action.select().where(
            User_action.username.contains(params['username']),
            User_action.actionTime > beginTime if beginTime != '' else True,
            User_action.actionTime < endTime if endTime != '' else True,
        ).order_by(User_action.updateAt.desc()).dicts())
        # print("输出", len(db))
        if db:
            result = list(db)
            return result
        else:
            return []
        # total=len(db)
        # result = {}
        # result['total'] = len(db)
        # data = db.offset((params.pageNo - 1) *
        #                  params.pageSize).limit(params.pageSize).dicts()
        # result["data"] = list(data)
        # return result
