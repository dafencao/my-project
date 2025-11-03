"""
纯增删改查操作,写在model里面
"""
import uuid
from datetime import datetime

import pytz

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, ForeignKeyField, TimeField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from peewee import fn, JOIN
import time

from models.user import Userinfo
from utils.tools_func import convert_arr, convert_num_arr


class AuditRecord(BaseModel):
    """
    审核记录表，
    """
    id = CharField(primary_key=True)
    auditBizId = CharField(column_name='audit_biz_id')
    userId = CharField(column_name='user_id')
    remark = CharField()
    auditType = CharField(column_name='audit_type')
    oldState = CharField(column_name='old_state')
    newState = CharField(column_name='new_state')
    result = CharField()

    class Meta:
        table_name = 'audit_record'  # 自定义映射的表名

    class Config:
        orm_mode = True

    @classmethod
    async def add_audit_record(cls, record):  # 添加审核记录
        # result = await async_db.execute(Department.create(**department))
        record['id'] = uuid.uuid1()
        record['createAt'] = datetime.strftime(
            datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        result = await async_db.create(AuditRecord,**record)
        return result.id

    @classmethod
    async def del_by_audit_record_id(cls, id):
        await async_db.execute(AuditRecord.delete().where(AuditRecord.id == id))

    @classmethod
    async def del_by_audit_bizId(cls, id):
        await async_db.execute(AuditRecord.delete().where(AuditRecord.auditBizId == id))
    @classmethod
    async def update_audit_record(cls, department):
        # 字典结构更新数据
        print(department)
        u = await async_db.execute(AuditRecord.update(**department).where(AuditRecord.id == department['id']))
        #
        return u

    @classmethod
    async def fuzzy_query(cls, querydepartment):
        db = await async_db.execute(AuditRecord.select().where(AuditRecord.code.contains(querydepartment['code']),
                                       AuditRecord.name.contains(querydepartment['name'])).order_by(
            AuditRecord.createAt).dicts())
        result = list(db)
        return result
    # Department.name == querydepartment['name']
    @classmethod
    async def select_all(cls):  # 获取
        db = await async_db.execute(AuditRecord.select().dicts())
        # 附加 iterator() 方法调用还可以减少内存消耗
        return list(db)

    @classmethod
    async def select_last_record(cls,bizId,auditType):  # 获取
        db = await async_db.execute(AuditRecord.select(
            AuditRecord,
            Userinfo.realName
        ).join(
            Userinfo, JOIN.LEFT_OUTER,on=(AuditRecord.userId == Userinfo.account))
                        .where(AuditRecord.auditBizId==bizId,AuditRecord.auditType==auditType).order_by(AuditRecord.createAt.desc() ).dicts())
        # print(model_to_dict(db))
        if len(db)>0:
            return list(db)[0]
        else:
            return db