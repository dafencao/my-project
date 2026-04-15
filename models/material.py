from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, CharField, TextField, Model, AutoField
from playhouse.mysql_ext import JSONField


class Material(BaseModel):
    id = AutoField() 
    name = CharField(max_length=100, unique=True)
    source_software = CharField(max_length=50, default='JMatPro')
    description = TextField(null=True) 
    properties = JSONField() 
    class Meta:
        table_name = 'materials'
    class Config:
        orm_mode = True    
    

    @classmethod
    async def add_material(cls, material_dict):
        """异步添加材料信息到 MySQL"""
        # 直接利用异步驱动创建记录
        result = await async_db.create(cls, **material_dict)
        return result.id  # 返回主键 ID