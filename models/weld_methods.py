from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, CharField, TextField, Model, AutoField,IntegerField, DecimalField, DateTimeField,IntegrityError
from playhouse.mysql_ext import JSONField
from peewee import DoesNotExist
import datetime

class WeldingMethod(BaseModel):
    id = AutoField(primary_key=True)
    method_code = CharField(max_length=50, unique=True) # 代号唯一约束
    method_name = CharField(max_length=100)
    heat_source = CharField(max_length=50, null=True)
    shielding_gas = CharField(max_length=50, null=True)
    automation_level = CharField(max_length=50, null=True)
    description = TextField(null=True)
    
    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)

    class Meta:
        table_name = 'welding_methods'

    @classmethod
    async def add_method(cls, data: dict):
        try:
            result = await async_db.create(cls, **data)
            return True, result.id, "焊接方法添加成功"
        except IntegrityError:
            return False, None, f"方法代号 '{data.get('method_code')}' 已存在！"

    @classmethod
    async def delete_method(cls, method_id: int):
        try:
            obj = await async_db.get(cls, id=method_id)
            await async_db.delete(obj)
            return True, "删除成功"
        except DoesNotExist:
            return False, "未找到该焊接方法"

    @classmethod
    async def update_method(cls, method_id: int, update_data: dict):
        try:
            obj = await async_db.get(cls, id=method_id)
            for key, value in update_data.items():
                setattr(obj, key, value)
            await async_db.update(obj)
            return True, "更新成功"
        except DoesNotExist:
            return False, "未找到该焊接方法"
        except IntegrityError:
            return False, "更新失败：方法代号与其他记录冲突"

    @classmethod
    async def filter_methods(cls, code: str = None, name: str = None, page: int = 1, page_size: int = 10):
        query = cls.select()
        filters = []
        if code: filters.append(cls.method_code.contains(code))
        if name: filters.append(cls.method_name.contains(name))
            
        if filters: query = query.where(*filters)
            
        total = await async_db.count(query)
        query = query.order_by(cls.id.desc()).paginate(page, page_size)
        results = await async_db.execute(query)
        return results, total
    
    @classmethod
    async def get_all_methods(cls):
        """
        获取全量焊接方法列表 (不分页)
        通常用于前端的下拉选择框 (Select) 数据源
        """
        # 按 ID 倒序排列，确保最新添加的方法排在前面
        query = cls.select().order_by(cls.id.desc())
        return await async_db.execute(query)