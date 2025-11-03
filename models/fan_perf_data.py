from datetime import datetime

import pytz

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, FloatField, FloatField, fn, Model, IntegerField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from schemas.request import sys_user_schema
from utils.tools_func import tz


# from models.users import User
# 用户类


class PerfData(BaseModel):
    """
    性能曲线表
    """
    id = IntegerField(primary_key=True)
    modelId = CharField(column_name='model_id')
    fanId = CharField(column_name='fan_id')
    # model_id = ForeignKeyField(perf, 'model')
    flowRate = FloatField(column_name='flow_rate')
    fullPressure = FloatField(column_name='full_pressure')
    staticPressure = FloatField(column_name='static_pressure')
    fanEff = FloatField(column_name='fan_eff')
    staticPressureEff = FloatField(column_name='static_pressure_eff')
    shaftPower = FloatField(column_name='shaft_power')
    motorSpeed = FloatField(column_name='motor_speed')
    impellerDiameter = FloatField(column_name='impeller_diameter')
    noise = FloatField()
    specificSpeed = FloatField(column_name='specific_speed')
    u = FloatField()
    flowCoefficient = FloatField(column_name='flow_coefficient')
    pressureCoefficient = FloatField(column_name='pressure_coefficient')

    class Meta:
        table_name = 'fan_perf_data'

    class Config:
        orm_mode = True

    @classmethod
    async def get_perf_data_by_fan_id(cls, fanId: str):
        # print('get_perf_data:'+model)
        db = await async_db.execute(PerfData.select().where(
            PerfData.fanId == fanId).order_by(PerfData.flowRate).dicts())
        if db:
            return list(db)
        else:
            return []

    @classmethod
    async def get_perf_data_by_model(cls, model: str):
        # print('get_perf_data:'+model)
        db = await async_db.execute(PerfData.select().where(
            PerfData.modelId == model).dicts())
        if db:
            return list(db)
        else:
            return []

    @classmethod
    async def update_perf_data(cls, perf: Model):
        # print('perf')
        # print(perf)
        result = await async_db.execute(perf.save())
        return result

    @classmethod
    async def add_perf_datas(cls, perfDatas: list):

        async with db.atomic_async():
            for item in perfDatas:
                print('item')
                print(item)
                item['updateAt'] = datetime.strftime(
                    datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
                p = await async_db.create(PerfData, **item)

        # p = PerfData.insert_many(perf)
        # result = p.execute()
        return True

    @classmethod
    async def add_perf_data(cls, perf: dict):
        # print('perf')
        # print(perf)
        perf['noise'] = perf['noise'] if 'noise' in perf.keys(
        ) else None
        perf['modelId'] = perf['model']
        # perf = {
        #     'modelId': perf['model'],
        #
        #     'flowRate': perf['flowRate'],
        #
        #     'fullPressure': perf['fullPressure'],
        #     'staticPressure': perf['staticPressure'],
        #
        #     'fanEff': perf['fanEff'],
        #     'staticPressureEff': perf['staticPressureEff'],
        #
        #     'shaftPower': perf['shaftPower'],
        #     'motorSpeed': perf['motorSpeed'],
        #     'impellerDiameter': perf['impellerDiameter'],
        #     'noise': perf['noise'] if 'noise' in perf.keys(
        #     ) else None,
        #     'specificSpeed': perf['specificSpeed'],
        #     'u': perf['u'],
        #     'flowCoefficient': perf['flowCoefficient'],
        #     'pressureCoefficient': perf['pressureCoefficient']
        # }
        p = await async_db.create(PerfData, perf)
        # result = p.save()
        return p.id

    @classmethod
    async def del_perf_data(cls, fan_id_list):
        # print("fan_id_list")
        # print(fan_id_list)
        # db = Fan.delete .where(Fan.model == model).execute()
        db = await async_db.execute(PerfData.delete().where(PerfData.fanId.in_(
            fan_id_list)))

        return db
