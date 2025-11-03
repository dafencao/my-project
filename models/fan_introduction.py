

"""
纯增删改查操作，写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, ForeignKeyField, TimeField, BooleanField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from schemas.request import sys_user_schema

from peewee import fn, JOIN
import time
from schemas.response import resp
from utils.tools_func import convert_arr


class Fan_introduction(BaseModel):

    """
    风机产品介绍表 
    """
    id = IntegerField(primary_key=True)  # id
    name = CharField(column_name='name')  # 风机名称
    label = CharField(column_name='label')  # 风机类型
    coolObject = CharField(column_name='cool_object')  # 冷却对象
    description = CharField(column_name='description')  # 风机描述
    img = CharField(column_name='img')  # 风机图片路径
    train_type = IntegerField(column_name='train_type')  # 风机所属车辆类型
    remark = CharField(column_name='remark')  # 预留字段
    createBy = CharField(column_name='create_by')  # 创建用户
    updateBy = CharField(column_name='update_by')  # 更新用户
    createAt = CharField(column_name='create_at')  # 创建用户
    updateAt = CharField(column_name='update_at')  # 更新用户
    label_description = CharField(column_name='label_description')  # 更新用户
    sheet = CharField(column_name='sheet')  # 更新用户
    show = CharField()  # 更新用户
    class Meta:
        table_name = 'fan_introduction'  # 自定义映射的表名
    # 也可以根据类名选择表的名称
    # class Meta:
    #     database = db

    @classmethod
    async def fuzzy_query(cls, queryfan):

        # fn.abs(userinfo.full_pressure - queryUser.full_pressure).alias('count')

        db =await async_db.execute( Fan_introduction.select().dicts())

        # .order_by(
        #     # fn.abs(User.flow_rate-queryUser.flowRate),
        # )
        # db = db.offset((queryuserrole.current - 1) *
        #                queryuserrole.pageSize).limit(queryuserrole.pageSize)
        return list(db)


# 新增一条产品信息

    @classmethod
    async def add_fan(cls, fan):  # 添加风机信息
        result = await async_db.create(Fan_introduction,**fan)
        return result.id

# 通过id删除信息
    @classmethod
    async def del_fan(cls, id):
        await async_db.execute(Fan_introduction.delete().where(Fan_introduction.id ==
                                        id) )

  # 查询：查询所有信息

    @classmethod
    async def select_all(cls):
        # db = Fan_introduction.select(Fan_introduction.id, Fan_introduction.id).dicts()
        db =await async_db.execute( Fan_introduction.select().order_by(Fan_introduction.updateAt.desc(),Fan_introduction.createAt.desc()).dicts())
        return list(db)
    @classmethod
    async def select_by_trainType(cls, trainType):
        db =await async_db.execute( Fan_introduction.select().where(Fan_introduction.train_type == trainType).dicts())
        return list(db)
 # 查询：通过风机名称及分类查询信息
    @classmethod
    async def select_by_fan(cls, params):

        # if params
        # print("类型",params,params.label)
        # if params.label=="":
        # db = Fan_introduction.select().dicts()
        # else:
        db =await async_db.execute( Fan_introduction.select().where(Fan_introduction.label == params.label))
        # print("输出",len(db))
        # total=len(db)
        result = {}
        result['total'] = len(db)
        data = db.offset((params.current - 1) *
                         params.pageSize).limit(params.pageSize).dicts()
        result["data"] = list(data)
        return result

        # return list(db)
        # return model_to_dict(db)
        # db = User.select().where(User.account == account).dicts()
        # return db[0]

    @classmethod
    async def update_fan(cls, id, updatefan):
        # 字典结构更新风机名称数据
        # print("@@@@", id,updatefan)
        u =await async_db.execute( Fan_introduction.update(updatefan).where(Fan_introduction.id == id))
        # result = u.execute()
        return u


