import uuid

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, ForeignKeyField, DateTimeField, Model
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship

from models.fan_introduction import Fan_introduction
from models.userrole import Userrole
from schemas.request import sys_user_schema
from core import security
from peewee import fn, JOIN
import datetime


from utils.tools_func import convert_arr, convert_num_arr, convert_num_float_arr


# 机车位置控制

class IntroControl(BaseModel):
    """
    机车
    """
    id = CharField(primary_key=True)
    order = IntegerField()  # 部件序号
    trainType = IntegerField(column_name='train_type')  # 机车代号
    imagePosition = CharField(column_name='image_position')  # 部件图片位置
    circle = CharField()  # 圆圈位置
    linePoints = CharField(column_name='line_points')  # 连段关键点位置
    text = CharField()  # 文本位置
    circleNode = CharField(column_name='circle_node')  # 原点位置
    radius = IntegerField()  # 圆的半径
    show = IntegerField() #展示产品信息的id


    #

    createAt = DateTimeField(column_name='create_at')
    updateAt = DateTimeField(column_name='update_at')

    class Meta:
        table_name = 'intro_control'  # 映射到机车表

    @classmethod
    async def add_intro(cls, intro_control):  # 添加数据
        intro_control['id'] = str(uuid.uuid1())
        intro_control['radius'] = int(90)
        result = await async_db.create(IntroControl, **intro_control)
        # result = db.create(UserTest, **user_test)

        return result.id

    @classmethod
    async def del_by_intro_controlid(cls, intro_controlid):  # 通过id删除信息
        result = await async_db.execute(IntroControl.delete().where(IntroControl.id ==
                                                                    intro_controlid))
        return result

    @classmethod
    async def update_intro_control(cls, intro_control):  # 更新
        result = await async_db.update( intro_control )
        return result

    @classmethod
    async def select_by_intro_control_id(cls, id: str):  # id查询
        result = await async_db.execute(
            IntroControl.select(IntroControl.id,
                                IntroControl.trainType,
                                IntroControl.order,
                                fn.group_concat(IntroControl.imagePosition)
                                .python_value(convert_num_float_arr)
                                .alias('imagePosition'),
                                fn.group_concat(IntroControl.circle)
                                .python_value(convert_num_float_arr)
                                .alias('circle'),
                                fn.group_concat(IntroControl.linePoints)
                                .python_value(convert_num_float_arr)
                                .alias('linePoints'),
                                fn.group_concat(IntroControl.text)
                                .python_value(convert_num_float_arr)
                                .alias('text'),
                                fn.group_concat(IntroControl.circleNode)
                                .python_value(convert_num_float_arr)
                                .alias('circleNode'),
                                IntroControl.radius,
                                )
            # .join(IntroControl, JOIN.LEFT_OUTER,
            #       on=(IntroControl.id == id)
            #       )
            .order_by(IntroControl.trainType, IntroControl.order)
            .where(IntroControl.id == id).dicts())
        return list(result)

    @classmethod
    async def select_intro_control(cls):  # id查询
        result = await async_db.execute(
            IntroControl.select(IntroControl.id,
                                IntroControl.trainType,
                                IntroControl.order,
                                fn.group_concat(IntroControl.imagePosition)
                                .python_value(convert_num_float_arr)
                                .alias('imagePosition'),
                                fn.group_concat(IntroControl.circle)
                                .python_value(convert_num_float_arr)
                                .alias('circle'),
                                fn.group_concat(IntroControl.linePoints)
                                .python_value(convert_num_float_arr)
                                .alias('linePoints'),
                                fn.group_concat(IntroControl.text)
                                .python_value(convert_num_float_arr)
                                .alias('text'),
                                fn.group_concat(IntroControl.circleNode)
                                .python_value(convert_num_float_arr)
                                .alias('circleNode'),
                                IntroControl.radius,
                                IntroControl.show,
                                )
            # .join(IntroControl, JOIN.LEFT_OUTER,
            #       on=(IntroControl.id == id)
            #       )
            .group_by(IntroControl.id)
            .order_by(IntroControl.trainType, IntroControl.order)
            .dicts())
        return list(result)

# #动车位置控制
#
# class BulletControl(BaseModel):
#     """
#     机车
#     """
#     id = CharField()
#     sn = IntegerField()  # 部件序号
#     trainType = CharField(column_name='train_type')  # 动车代号
#     imagePosition = CharField(column_name='image_position')  # 部件图片位置
#     circle = CharField()  # 圆圈位置
#     linePoint = CharField(column_name='line_point')  # 连段关键点位置
#     text = CharField()  # 文本位置
#     circleNode = CharField(column_name='circle_node')  # 原点位置
#     radius = IntegerField()  # 圆的半径
#
#     createAt = DateTimeField(column_name='create_at')
#     updateAt = DateTimeField(column_name='update_at')
#
#     class Meta:
#         table_name = 'bullet_control'  # 映射到动车表
#
#
#     @classmethod
#     async def add_bullet(cls, bullet_control):  # 添加动车数据
#         result = await async_db.create(BulletControl, **bullet_control)
#         # result = db.create(UserTest, **user_test)
#
#         return result.id
#
#     @classmethod
#     async def del_by_bullet_controlid(cls, bullet_controlid):  # 通过id删除信息
#         result = await async_db.execute(BulletControl.delete().where(BulletControl.id ==
#                                                                       bullet_controlid))
#         return result
#
#     @classmethod
#     async def update_bullet_control(cls, bullet_control: Model):  # 更新
#         result = await async_db.update(bullet_control)
#         return result
#
#     @classmethod
#     async def select_by_bullet_control_id(cls, id: int):  # id查询
#         result = await async_db.execute(
#             BulletControl.select(
#                                   fn.group_concat(BulletControl.sn)
#                                   .python_value(convert_num_float_arr)
#                                   .alias('sn'),
#                                   fn.group_concat(BulletControl.trainType)
#                                   .python_value(convert_num_float_arr)
#                                   .alias('trainType'),
#                                   # fn.group_concat(BulletControl.imagePosition)
#                                   # .python_value(convert_num_float_arr)
#                                   # .alias('imagePosition'),
#                                   fn.group_concat(BulletControl.circle)
#                                   .python_value(convert_num_float_arr)
#                                   .alias('circle'),
#                                   fn.group_concat(BulletControl.linePoint)
#                                   .python_value(convert_num_float_arr)
#                                   .alias('linePoint'),
#                                   fn.group_concat(BulletControl.text)
#                                   .python_value(convert_num_float_arr)
#                                   .alias('text'),
#                                   fn.group_concat(BulletControl.circleNode)
#                                   .python_value(convert_num_float_arr)
#                                   .alias('circleNode'),
#                                   fn.group_concat(BulletControl.radius)
#                                   .python_value(convert_num_float_arr)
#                                   .alias('radius')
#                                   )
#             # .join(BulletControl, JOIN.LEFT_OUTER,
#             #       on=(BulletControl.id == id)
#             #       )
#             .group_by(BulletControl.id)
#             .where(BulletControl.id == id).dicts())
#         return list(result)
