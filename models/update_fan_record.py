from datetime import datetime

import pytz
from peewee import JOIN, Model, fn, CharField

from common.session import async_db, BaseModel
from models.audit import AuditRecord
from models.fan import Fan, FanCategory


class FanUpdateRecord(Fan):
    class Meta:
        table_name = "update_fan_record"
        legacy_table_names = False

    class Config:
        orm_mode = True

    @classmethod
    async def fuzzy_query_by_dict(cls, queryFan, isPagenation: bool = True):
        res = await async_db.execute(FanCategory.select().where(FanCategory.name == queryFan['categoryId']).dicts())
        # res = await async_db.execute(FanCategory.select().where(FanCategory.name == queryFan['category']).dicts())
        res = list(res)
        print('res')
        print(res)
        if len(res) == 0:
            categoryId = None
        else:
            categoryId = res[0]['id']
        # print('categoryId')
        # print(categoryId)
        if queryFan['status'] is None:
            queryFan['status'] = []
        if True:
            db = await async_db.execute(
                FanUpdateRecord.select(
                    FanUpdateRecord,
                    # FanCategory.series.alias('categoryId'),
                    # FanCategory.name,
                    FanCategory.name.alias('category')
                ).where(
                    # FanUpdateRecord.applicationModelId.not_in(applicationModelIdList) if queryFan['applicationModelId'] == '其他'else FanUpdateRecord.applicationModelId.contains(
                    #     queryFan['applicationModelId']),
                    FanUpdateRecord.applicationModelId.contains(
                        queryFan['applicationModelId']),
                    # FanUpdateRecord.applicationModel.contains(queryFan['applicationModel']),
                    # FanUpdateRecord.seriesId.contains(queryFan['categoryId']),
                    FanCategory.parentId == categoryId if categoryId else True,
                    # FanUpdateRecord.category.contains(queryFan['category']) ,
                    (FanCategory.name == queryFan['category']
                     ) if queryFan['category'] else True,
                    # # FanUpdateRecord.coolObject.not_in(coolObjectList)if queryFan['coolObject'] == '其他' else FanUpdateRecord.coolObject.contains(
                    # #     queryFan['coolObject']),
                    # # FanUpdateRecord.coolObjectId.contains(queryFan['coolObject']),
                    (FanUpdateRecord.coolObject ==
                     queryFan['coolObject']) if queryFan['coolObject'] else True,
                    FanUpdateRecord.model.contains(queryFan['model']),
                    FanUpdateRecord.figNum.contains(queryFan['figNum']),
                    FanUpdateRecord.version.contains(queryFan['version']),
                    FanUpdateRecord.status.in_(queryFan['status']) if len(queryFan['status']) > 0 else True,
                    # FanUpdateRecord.status.not_in(queryFan['excludeStatus']) if queryFan['excludeStatus'] else True,
                    FanUpdateRecord.status.not_in(queryFan['excludeStatus']) if not queryFan['excludeStatus'] is None else True,
                    (FanUpdateRecord.createBy == queryFan['createBy']) if queryFan['createBy'] else True,
                    (FanUpdateRecord.createBy != queryFan['currentUser']) if queryFan['currentUser'] else True
                ).join(
                    FanCategory, JOIN.LEFT_OUTER, on=(
                            FanUpdateRecord.seriesId == FanCategory.id)
                ).order_by(
                    # fn.abs(FanUpdateRecord.flowRate - queryFan['flowRate']),
                    # fn.abs(FanUpdateRecord.fullPressure - queryFan['fullPressure']),
                    # fn.abs(FanUpdateRecord.efficiency - queryFan['efficiency']),
                    # fn.abs(FanUpdateRecord.flowRate - queryFan['shaftPower']),
                    # fn.abs(FanUpdateRecord.motorSpeed - queryFan['motorSpeed']),
                    # fn.abs(FanUpdateRecord.altitude - queryFan['altitude']),
                    # fn.abs(FanUpdateRecord.temperature - queryFan['temperature']),
                    FanUpdateRecord.updateAt.desc()
                ).dicts())
        if isPagenation:
            db = db.offset((queryFan['current'] - 1) *
                           queryFan['pageSize']).limit(queryFan['pageSize'])
        # SQL('voltage').desc()
        # print(db.sql())
        return list(db)

    @classmethod
    async def similar_fuzzy_query_by_dict(cls, queryFan, categoryList, isPagenation: bool = True):

        # fn.abs(FanUpdateRecord.fullPressure - queryFan.fullPressure).alias('count')
        print(categoryList != None)
        try:
            db = await async_db.execute(FanUpdateRecord.select(FanUpdateRecord,
                                                               # FanCategory.series.alias('categoryId'),
                                                               # FanCategory.name,
                                                               FanCategory.name.alias('category')).where(

                # FanUpdateRecord.applicationModelId.not_in(applicationModelIdList) if queryFan['applicationModelId'] == '其他'else FanUpdateRecord.applicationModelId.contains(
                #     queryFan['applicationModelId']),
                FanUpdateRecord.applicationModelId.contains(
                    queryFan['applicationModelId']),
                FanUpdateRecord.applicationModel.contains(queryFan['applicationModel']),
                # FanCategory.series.contains(queryFan['categoryId']),
                # FanUpdateRecord.category.contains(queryFan['category']) ,
                # FanCategory.name == queryFan['category']if queryFan['category'] else True,
                # FanUpdateRecord.coolObject.not_in(coolObjectList)if queryFan['coolObject'] == '其他' else FanUpdateRecord.coolObject.contains(
                #     queryFan['coolObject']),
                # FanUpdateRecord.coolObjectId.contains(queryFan['coolObject']),
                FanUpdateRecord.coolObject == (
                    queryFan['coolObject']) if queryFan['coolObject'] else True,
                FanUpdateRecord.model.contains(queryFan['model']),
                FanUpdateRecord.figNum.contains(queryFan['figNum']),

                FanCategory.id.in_(categoryList) | FanCategory.parentId.in_(
                    categoryList) if categoryList != None else True,
            ).join(
                FanCategory, JOIN.LEFT_OUTER, on=(
                        FanUpdateRecord.seriesId == FanCategory.id)
            ).order_by(
                fn.abs(FanUpdateRecord.flowRate - queryFan['flowRate']),
                fn.abs(FanUpdateRecord.fullPressure - queryFan['fullPressure']),
                fn.abs(FanUpdateRecord.efficiency - queryFan['efficiency']),
                fn.abs(FanUpdateRecord.flowRate - queryFan['shaftPower']),
                fn.abs(FanUpdateRecord.motorSpeed - queryFan['motorSpeed']),
                fn.abs(FanUpdateRecord.altitude - queryFan['altitude']),
                fn.abs(FanUpdateRecord.temperature - queryFan['temperature']),
                FanUpdateRecord.createAt.desc()

            ).dicts())
        except Exception as e:
            print(str(e))

        if isPagenation:
            db = db.offset((queryFan['current'] - 1) *
                           queryFan['pageSize']).limit(queryFan['pageSize'])
        # SQL('voltage').desc()
        # print(db.sql())
        return list(db)

    @classmethod
    async def add_fan_by_dict(cls, fan: dict):
        result = await async_db.create(FanUpdateRecord, **fan)
        return result.id

    @classmethod
    async def update_fan(cls, fan: Model):

        result = await async_db.update(fan)
        return result

    @classmethod
    async def del_fan(cls, id_list):
        print("id_list")
        print(id_list)
        db = await async_db.execute(FanUpdateRecord.delete().where(FanUpdateRecord.id.in_(
            id_list)))

        return db

    @classmethod
    async def single_by_id(cls, id: str):
        result = await async_db.execute(FanUpdateRecord.select(
            FanUpdateRecord,
            FanCategory.parentId.alias('categoryParentId'),
            FanCategory.id.alias('categoryId'),
            FanCategory.name.alias('category'),
        ).join(
            FanCategory, JOIN.LEFT_OUTER, on=(FanUpdateRecord.seriesId == FanCategory.id)
        ).where(FanUpdateRecord.id == id).limit(1).dicts())
        # if result is None:
        #     return None
        # result = list(result)
        if len(result) == 0:
            return None
        return list(result)[0]


class FanUpdateRecordRelp(BaseModel):
    id = CharField(primary_key=True)
    version = CharField()
    type = CharField()
    remark = CharField()
    fanId = CharField(column_name='fan_id')
    copyId = CharField(column_name='copy_id')

    class Meta:
        table_name = "update_fan_record_relp"
        legacy_table_names = False

    class Config:
        orm_mode = True

    @classmethod
    async def add(cls, record):
        record['createAt'] = datetime.strftime(datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        result = await async_db.create(FanUpdateRecordRelp, **record)
        return result.id

    @classmethod
    async def query_by_id(cls, id):
        result = await async_db.execute(FanUpdateRecordRelp.select().where(FanUpdateRecordRelp.id == id).dicts())
        result = list(result)
        if len(result) == 0:
            return None
        return result[0]

    @classmethod
    async def query_by_fan_id(cls, id):

        result = await async_db.execute(
            FanUpdateRecordRelp.select(
                FanUpdateRecordRelp,
                FanUpdateRecord.status
            ).join(
                FanUpdateRecord,
                JOIN.LEFT_OUTER,
                on=(FanUpdateRecord.id == FanUpdateRecordRelp.id)
            ).where(
                FanUpdateRecordRelp.fanId == id,
                FanUpdateRecord.status.in_(['pass','passed'])
            ).order_by(
                FanUpdateRecordRelp.createAt.desc()
            ).dicts())
        result = list(result)

        recordList = []
        # for item in result:
        #     recordList.append(item['id'])
        # recordFanList = await async_db.execute(
        #     Fan.select(
        #     ).where(
        #         FanUpdateRecord.id.in_(recordList),
        #         FanUpdateRecord.status.in_(['pass','passed']
        #                                    )).order_by(
        #         FanUpdateRecordRelp.createAt.desc()
        #     ).dicts())
        # recordFanList = list(recordFanList)
        return result
        # AuditRecord, AuditRecord.createAt.alias('auditRecordCreateAt')
        #
        # AuditRecord.name.alias('status'),
        # .join(
        #     AuditRecord, JOIN.LEFT_OUTER, on=(FanUpdateRecordRelp.id == AuditRecord.auditBizId)).where(
        #     FanUpdateRecordRelp.fanId == id
        # )
        # AuditRecord.createAt.desc(),

        # result = await async_db.execute(
        #     FanUpdateRecordRelp.select(
        #         FanUpdateRecordRelp,
        #     ).where(
        #     FanUpdateRecordRelp.fanId == id).order_by(
        #         FanUpdateRecordRelp.createAt.desc()
        #     ).dicts())
        # # .group_by(FanUpdateRecordRelp.id)
        # result = list(result)
        # for item in result:
        #     db = await async_db.execute(AuditRecord.select().where(AuditRecord.auditBizId == id).order_by(
        #         AuditRecord.createAt.desc()).dicts())
        #     # print(model_to_dict(db))
        #     if len(db) > 0:
        #         res = list(db)[0]
        #     else:
        #         res = db
        #     print('res')
        #     print(res)
        #     item['status'] = res['result']
        # if len(result) == 0:
        #     return []
        # return result

    @classmethod
    async def delete_by_id(cls, id):
        db = await async_db.execute(FanUpdateRecordRelp.delete().where(FanUpdateRecord.id == id))
        return db
