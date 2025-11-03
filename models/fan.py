'''
Author: 嘉欣 罗 2592734121@qq.com
Date: 2022-12-23 11:00:13
LastEditors: Please set LastEditors
LastEditTime: 2023-05-09 14:45:49
FilePath: \psad-backend\models\fans.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''

from datetime import datetime
import time

from math import fabs
from typing import List

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField
from sqlalchemy.orm import relationship
from peewee import *
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
# from peewee import fn
import threading

lock = threading.Lock()


# 风机类型表


class FanCategory(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    # series = CharField(column_name='category')
    code = CharField(column_name='code')
    parentId = IntegerField(column_name='parent_id')

    sort = IntegerField()

    # update_at = TimeField()

    class Meta:
        table_name = "fan_category"

    class Config:
        orm_mode = True

    @classmethod
    async def group_all(cls):
        # , fn.group_concat(FanCategory.name).alias('count')
        db = await async_db.execute(FanCategory.select(FanCategory.name, FanCategory.category).group_by(
            FanCategory.category).dicts())
        result = list(db)
        print('result')
        print(result)

    @classmethod
    async def select_all(cls):
        db = await async_db.execute(FanCategory.select(FanCategory.name).dicts())  # .iterator()
        # 附加 iterator() 方法调用还可以减少内存消耗
        if db:
            return db
        else:
            return list(db)

    @classmethod
    async def select_group_all(cls):
        db = await async_db.execute(FanCategory.select().dicts())  # .iterator()
        # 附加 iterator() 方法调用还可以减少内存消耗
        if db:
            result = list(db)
        else:
            result = []
        return result

    @classmethod
    async def add(cls, category):
        result = await async_db.create(FanCategory, **category)
        return result.id

    # @classmethod
    # async def update(cls, name):
    #     print("update name")
    #     print(name)
    #
    #     c = await async_db.execute(FanCategory.create(name=name, update_at=time.time()))
    #     result = c.save()
    #     return result

    # category:List

    # @classmethod
    # async def select_id_by_series_and_name(cls, series, name):
    #     # print('category1')
    #     # print(category)
    #     db = await async_db.execute(
    #         FanCategory.select(FanCategory.id).where(
    #             FanCategory.series == series, FanCategory.name == name).dicts())
    #     db = list(db)
    #     print(db)
    #
    #     return db[0]

    @classmethod
    async def fuzzy_query(cls, query):
        db = await async_db.execute(
            FanCategory.select().where(
                # FanCategory.series.contains(query['series']),
                FanCategory.name.contains(query['name'])).order_by(
                FanCategory.sort, FanCategory.code).dicts())
        result = list(db)
        return result

    @classmethod
    async def add_category(cls, category):  # 添加角色
        # result = await async_db.execute(Department.create(**department))
        result = await async_db.create(FanCategory, **category)
        return result.id

    @classmethod
    async def del_by_category_id(cls, id):
        await async_db.execute(FanCategory.delete().where(FanCategory.id == id))

    @classmethod
    async def update_category(cls, category):
        # 字典结构更新数据
        print(category)
        res = await async_db.execute(FanCategory.select().where(FanCategory.id == category['id']).dicts())
        print('res')
        print(list(res))
        # u = await async_db.execute(FanCategory.update(**category).where(FanCategory.id == category['id']))
        #
        category = dict_to_model(FanCategory, category)
        await async_db.update(category)
        # return u

        # category = dict_to_model(FanCategory,category)
        # print(category)
        # u = await async_db.update(category)
        # #
        # return u


# 风机应用车型表
class FanApplicationModel(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    code = CharField()

    # update_at = TimeField()

    class Meta:
        table_name = "fan_application_model"

    class Config:
        orm_mode = True

    @classmethod
    async def select_all(cls):
        db = await async_db.execute(FanApplicationModel.select().dicts())  # .iterator()
        # 附加 iterator() 方法调用还可以减少内存消耗
        if db:
            return list(db)
        else:
            return []

    @classmethod
    async def add(cls, code, name):
        # print("add name")
        # print(name)

        result = await async_db.execute(FanApplicationModel.create(code=code,
                                                                   name=name))
        return result.id

    @classmethod
    async def update_one(cls, origin_name, new_name):

        record = await async_db.execute(FanApplicationModel.select().where(
            FanApplicationModel.name == origin_name).first())
        record = model_to_dict(record)
        id = record['id']
        f = FanApplicationModel(id=id, name=new_name)
        result = f.save()
        return result

    @classmethod
    async def model_update_one(cls, fanApplModel):

        result = fanApplModel.save()
        return result

    @classmethod
    async def delete_by_id(cls, id):
        result = await async_db.execute(FanApplicationModel.delete().where(FanApplicationModel.id == id))
        return result


# 风机冷却对象表
class FanCoolObject(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    code = CharField()

    # update_at = TimeField()

    class Meta:
        table_name = "fan_cool_object"

    class Config:
        orm_mode = True

    @classmethod
    async def select_all(cls):
        db = await async_db.execute(FanCoolObject.select().dicts())
        if db:
            return db
        else:
            return []

    @classmethod
    async def add(cls, name):
        result = await async_db.execute(FanCoolObject.create(name=name, update_at=time.time()))
        # result = c.save()
        return result.id

    @classmethod
    async def update(cls, name):
        c = await async_db.execute(FanCoolObject.create(name=name, update_at=time.time()))
        result = c.save()
        return result


# 风机类
class Fan(BaseModel):
    """
    风机表
    """

    id = CharField(primary_key=True)
    # applicationModelId = IntegerField( column_name='application_model_id')
    applicationModelId = ForeignKeyField(
        FanApplicationModel, 'name', column_name='application_model_id')

    applicationModel = CharField(column_name='application_model')
    # category = CharField()
    seriesId = ForeignKeyField(
        FanCategory, 'name', verbose_name='风机系列', backref='category', column_name='category_id')
    # category = CharField()
    coolObject = ForeignKeyField(
        FanCoolObject, 'name', column_name='cool_object')
    #
    coolObjectId = IntegerField(column_name='cool_object_id')
    # model = CharField(primary_key=True)
    model = CharField()
    figNum = CharField(column_name='fig_num')
    version = CharField()

    flowRate = FloatField(column_name='flow_rate')

    fullPressure = FloatField(column_name='full_pressure')
    staticPressure = FloatField(column_name='static_pressure')

    shaftPower = FloatField(column_name='shaft_power')
    efficiency = FloatField()

    motorModel = CharField(column_name='motor_model')
    powerFrequency = FloatField(column_name='power_frequency')

    motorPower = FloatField(column_name='motor_power')
    motorSpeedMin = IntegerField(column_name='motor_speed_min')
    motorSpeed = IntegerField(column_name='motor_speed')

    # ratedVoltage = IntegerField(column_name='rated_voltage')
    ratedVoltage = CharField(column_name='rated_voltage')
    ratedCurrent = IntegerField(column_name='rated_current')

    temperature = FloatField()
    altitude = FloatField()
    humidity = FloatField()

    impellerDiameter = FloatField(column_name='impeller_diameter')
    weight = FloatField()

    impellerOuterDiameter = FloatField(column_name='impeller_outer_diameter')
    impellerInnerDiameter = FloatField(column_name='impeller_inner_diameter')
    impellerOutlet = FloatField(column_name='impeller_outlet')
    impellerInlet = FloatField(column_name='impeller_inlet')
    exitCorner = FloatField(column_name='exit_corner')
    inletCorner = FloatField(column_name='inlet_corner')
    impellerNumber = IntegerField(column_name='impeller_number')

    remark1 = CharField()
    remark2 = CharField()
    sampleDesc = CharField(column_name='sample_desc')
    status = CharField()

    imgOutline = CharField(column_name='img_outline')
    img3d = CharField()
    perfExcel = CharField(column_name='perf_excel')
    createBy = CharField(column_name='create_by')
    updateBy = CharField(column_name='update_by')

    # items = relationship("User", back_populates="owner")

    class Meta:
        table_name = "fan"
        legacy_table_names = False

    class Config:
        orm_mode = True

    @classmethod
    async def group_by_category(cls):
        # ######显示无记录分类显示############

        # applicationModel = FanApplicationModel.select(
        #     FanApplicationModel.name).dicts()
        # print('applicationModel')
        # print(applicationModel)

        # coolObject = FanCoolObject.select(FanCoolObject.name).dicts()
        # print('coolObject')
        # print(coolObject)

        # categorys = FanCategory.select(FanCategory.name).dicts()
        # print("categorys")
        # print(categorys)

        # applicationModel = list(applicationModel)
        # coolObject = list(coolObject)
        # categorys = list(categorys)

        # result = {}
        # for model in applicationModel:
        #     m = model['name']
        #     result[m] = {}
        # print('result1')
        # print(result)
        # for key in result:
        #     for object in coolObject:
        #         o = object['name']
        #         result[key][o] = {}
        # db = list(Fan.select(
        #     Fan.applicationModel, Fan.coolObject, Fan.category, fn.group_concat(
        #         Fan.model)
        # ).group_by(Fan.applicationModel, Fan.coolObject, Fan.category,).dicts())
        # print('group_by_category_result')
        # print(db)
        # for key in result:
        #     for object in coolObject:
        #         o = object['name']
        #         for category in categorys:
        #             c = category['name']
        #             for item in db:
        #                 if key == item['applicationModel'] and o == item['coolObject'] and c == item['category']:
        #                     result[key][o][c] = item['model'].split(',')
        # return result
        # ######显示无数据的分类显示############
        result = await async_db.execute(FanCategory.select(FanCategory.id, FanCategory.name).dicts())

        categoryDict = {}
        result = list(result)
        for item in result:
            categoryDict[item['id']] = item['name']
        db = await async_db.execute(Fan.select(
            Fan.id,
            Fan.applicationModelId,
            Fan.coolObject,
            # Fan.seriesId.alias('categoryId'),
            # FanCategory.name.alias('category'),
            fn.group_concat(FanCategory.name).alias('category'),
            FanCategory.parentId,  # .alias('categoryId'),

        ).join(
            FanCategory, JOIN.LEFT_OUTER, on=(Fan.seriesId == FanCategory.id)
        ).group_by(Fan.applicationModelId, Fan.coolObject, FanCategory.name).dicts())
        # FanCategory.category,Fan.seriesId,
        # print('db')
        # print(db)
        if db:
            result = list(db)
        else:
            result = []
        res = {}
        temp = []
        for item in result:
            if item['parentId'] == 0:
                continue
            item['categoryId'] = categoryDict[item['parentId']]
            temp.append(item)
        result = temp
        for item in result:
            if item['applicationModelId'] not in res.keys():
                res[item['applicationModelId']] = {}
            if item['coolObject'] not in res[item['applicationModelId']].keys():
                res[item['applicationModelId']][item['coolObject']] = {}
            if item['categoryId'] not in res[item['applicationModelId']][item['coolObject']].keys():
                res[item['applicationModelId']
                ][item['coolObject']][item['categoryId']] = {}
            # print(item['applicationModelId'])
            # print(item['coolObject'])
            # print(item['categoryId'])
            # print(res[item['applicationModelId']]
            #       [item['coolObject']][item['categoryId']])
            if item['category'] not in res[item['applicationModelId']][item['coolObject']][item['categoryId']]:
                # res[item['applicationModelId']
                #     ][item['coolObject']][item['categoryId']][item['category']] = {}
                print(item['category'])
                res[item['applicationModelId']][item['coolObject']][item['categoryId']
                ] = set(item['category'].split(','))

        return res

    @classmethod
    async def fuzzy_query_by_dict(cls, queryFan, isPagenation: bool = True):
        res = await async_db.execute(FanCategory.select().where(FanCategory.name == queryFan['categoryId']).dicts())
        res = list(res)
        if len(res) == 0:
            categoryId = None
        else:
            categoryId = res[0]['id']
        # print('categoryId')
        # print(categoryId)
        print("")
        print(queryFan['sortedByModel'])
        print(queryFan['sortedByModel'] is None)
        if True:
            db = await async_db.execute(
                Fan.select(
                    Fan,
                    # FanCategory.series.alias('categoryId'),
                    # FanCategory.name,
                    FanCategory.name.alias('category')
                ).where(
                    # Fan.applicationModelId.not_in(applicationModelIdList) if queryFan['applicationModelId'] == '其他'else Fan.applicationModelId.contains(
                    #     queryFan['applicationModelId']),
                    Fan.applicationModelId.contains(
                        queryFan['applicationModelId']),
                    # Fan.applicationModel.contains(queryFan['applicationModel']),
                    # Fan.seriesId.contains(queryFan['categoryId']),
                    FanCategory.parentId == categoryId if categoryId else True,
                    # Fan.category.contains(queryFan['category']) ,
                    (FanCategory.name == queryFan['category']
                     ) if queryFan['category'] else True,
                    # # Fan.coolObject.not_in(coolObjectList)if queryFan['coolObject'] == '其他' else Fan.coolObject.contains(
                    # #     queryFan['coolObject']),
                    # # Fan.coolObjectId.contains(queryFan['coolObject']),
                    (Fan.coolObject ==
                     queryFan['coolObject']) if queryFan['coolObject'] else True,
                    Fan.model.contains(queryFan['model']),
                    Fan.figNum.contains(queryFan['figNum']),
                    Fan.version.contains(queryFan['version']),
                    Fan.status.in_(queryFan['status']) if len(queryFan['status']) > 0 else True,
                    (Fan.createBy == queryFan['createBy']) if queryFan['createBy'] else True
                ).join(
                    FanCategory, JOIN.LEFT_OUTER, on=(
                            Fan.seriesId == FanCategory.id)
                ).order_by(
                    fn.abs(Fan.flowRate - queryFan['flowRate']),
                    fn.abs(Fan.fullPressure - queryFan['fullPressure']),
                    fn.abs(Fan.efficiency - queryFan['efficiency']),
                    fn.abs(Fan.flowRate - queryFan['shaftPower']),
                    fn.abs(Fan.motorSpeed - queryFan['motorSpeed']),
                    fn.abs(Fan.altitude - queryFan['altitude']),
                    fn.abs(Fan.temperature - queryFan['temperature']),
                    Fan.model if queryFan['sortedByModel'] is not None else Fan.updateAt.desc()
                ).dicts())
        if isPagenation:
            db = db.offset((queryFan['current'] - 1) *
                           queryFan['pageSize']).limit(queryFan['pageSize'])
        # SQL('voltage').desc()
        # print(db.sql())
        return list(db)

    @classmethod
    async def change_fuzzy_query_by_dict(cls, queryFan, categoryList, isPagenation: bool = True):

        print(categoryList != None)
        try:
            db = await async_db.execute(Fan.select(Fan,
                                                   FanCategory.name.alias('category')).where(
                Fan.applicationModelId.contains(
                    queryFan['applicationModelId']),
                Fan.applicationModel.contains(queryFan['applicationModel']),
                Fan.coolObject == (
                    queryFan['coolObject']) if queryFan['coolObject'] else True,
                Fan.model.contains(queryFan['model']),
                Fan.figNum.contains(queryFan['figNum']),

                FanCategory.id.in_(categoryList) | FanCategory.parentId.in_(
                    categoryList) if categoryList != None else True,
            ).join(
                FanCategory, JOIN.LEFT_OUTER, on=(
                        Fan.seriesId == FanCategory.id)
            ).order_by(
                Fan.createAt.desc()
            ).dicts())
        except Exception as e:
            print(str(e))
            return []
        if isPagenation:
            db = db.offset((queryFan['current'] - 1) *
                           queryFan['pageSize']).limit(queryFan['pageSize'])
        # SQL('voltage').desc()
        # print(db.sql())
        return list(db)

    @classmethod
    async def similar_fuzzy_query_by_dict(cls, queryFan, categoryList, isPagenation: bool = True):
        # 联表模糊查询并排序
        # fn.abs(Fan.fullPressure - queryFan.fullPressure).alias('count')
        print(categoryList != None)
        try:
            db = await async_db.execute(Fan.select(Fan,
                                                   # FanCategory.series.alias('categoryId'),
                                                   # FanCategory.name,
                                                   FanCategory.name.alias('category')).where(

                # Fan.applicationModelId.not_in(applicationModelIdList) if queryFan['applicationModelId'] == '其他'else Fan.applicationModelId.contains(
                #     queryFan['applicationModelId']),
                Fan.applicationModelId.contains(
                    queryFan['applicationModelId']),
                Fan.applicationModel.contains(queryFan['applicationModel']),
                # FanCategory.series.contains(queryFan['categoryId']),
                # Fan.category.contains(queryFan['category']) ,
                # FanCategory.name == queryFan['category']if queryFan['category'] else True,
                # Fan.coolObject.not_in(coolObjectList)if queryFan['coolObject'] == '其他' else Fan.coolObject.contains(
                #     queryFan['coolObject']),
                # Fan.coolObjectId.contains(queryFan['coolObject']),
                Fan.coolObject == (
                    queryFan['coolObject']) if queryFan['coolObject'] else True,
                Fan.model.contains(queryFan['model']),
                Fan.figNum.contains(queryFan['figNum']),

                FanCategory.id.in_(categoryList) | FanCategory.parentId.in_(
                    categoryList) if categoryList != None else True,
            ).join(
                FanCategory, JOIN.LEFT_OUTER, on=(
                        Fan.seriesId == FanCategory.id)
            ).order_by(
                # fn.abs(Fan.flowRate - queryFan['flowRate']),
                # fn.abs(Fan.fullPressure - queryFan['fullPressure']),
                # fn.abs(Fan.efficiency - queryFan['efficiency']),
                # fn.abs(Fan.flowRate - queryFan['shaftPower']),
                # fn.abs(Fan.motorSpeed - queryFan['motorSpeed']),
                # fn.abs(Fan.altitude - queryFan['altitude']),
                # fn.abs(Fan.temperature - queryFan['temperature']),
                Fan.createAt.desc()
            ).dicts())
        except Exception as e:
            print(str(e))
            return []
        if isPagenation:
            db = db.offset((queryFan['current'] - 1) *
                           queryFan['pageSize']).limit(queryFan['pageSize'])
        # SQL('voltage').desc()
        # print(db.sql())
        return list(db)



    @classmethod
    async def add_fan_by_dict(cls, fan: dict):
        result = await async_db.create(Fan, **fan)
        return result.id

    @classmethod
    async def update_fan(cls, fan: Model):

        result = await async_db.update(fan)
        return result

    @classmethod
    async def del_fan(cls, id_list):
        print("id_list")
        print(id_list)
        # db = Fan.delete .where(Fan.model == model).execute()
        db = await async_db.execute(Fan.delete().where(Fan.id.in_(
            id_list)))

        return db

    @classmethod
    async def single_by_model(cls, modelId: str):
        result = await async_db.execute(Fan.select(
            Fan,
            FanCategory.parentId.alias('categoryParentId'),
            FanCategory.id.alias('categoryId'),
            FanCategory.name.alias('category'),
            # FanCategory.series.alias('categoryId'),
        ).join(
            FanCategory, JOIN.LEFT_OUTER, on=(Fan.seriesId == FanCategory.id)
        ).where(Fan.id == modelId).limit(1).dicts())
        if result is None:
            return None
        result = list(result)
        if len(result) == 0:
            return None
        return result[0]

    @classmethod
    async def select_by_model(cls, model: str):
        result = await async_db.execute(Fan.select(Fan.id, Fan.model).where(Fan.model == model).dicts())
        result = list(result)
        if result is None:
            return None
        if len(result) == 0:
            return []
        return result

    @classmethod
    async def single_by_id(cls, id: str):
        result = await async_db.execute(Fan.select(
            Fan,
            FanCategory.parentId.alias('categoryParentId'),
            FanCategory.id.alias('categoryId'),
            FanCategory.name.alias('category'),
        ).join(
            FanCategory, JOIN.LEFT_OUTER, on=(Fan.seriesId == FanCategory.id)
        ).where(Fan.id == id).limit(1).dicts())
        # if result is None:
        #     return None
        # result = list(result)
        if len(result) == 0:
            return None
        return list(result)[0]
