from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, CharField, TextField, Model, AutoField,IntegrityError
from playhouse.mysql_ext import JSONField
from peewee import DoesNotExist


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
    

    # --- 1. 纯新增 ---
    @classmethod
    async def add_material(cls, material_dict: dict):
        """仅限新增，如果名称已存在则报错"""
        try:
            result = await async_db.create(cls, **material_dict)
            return True, result.id, "材料添加成功"
        except IntegrityError:
            # 捕获 unique=True 导致的报错
            return False, None, f"材料名称 '{material_dict.get('name')}' 已存在，请勿重复录入"

    # --- 2. 纯更新 ---
    @classmethod
    async def update_material(cls, material_id: int, update_data: dict):
        """根据 ID 仅更新已有材料"""
        try:
            material_obj = await async_db.get(cls, id=material_id)
            
            # 更新基础字段
            if "name" in update_data: material_obj.name = update_data["name"]
            if "source_software" in update_data: material_obj.source_software = update_data["source_software"]
            if "description" in update_data: material_obj.description = update_data["description"]
            
            # 对于 JSON 字段，执行增量合并更新 (避免覆盖掉没传的旧参数)
            if "properties" in update_data:
                new_props = update_data["properties"]
                old_props = material_obj.properties or {}
                old_props.update(new_props)
                material_obj.properties = old_props
            
            await async_db.update(material_obj)
            return True, "材料更新成功"
        except DoesNotExist:
            return False, f"未找到 ID 为 {material_id} 的材料"
        except IntegrityError:
            return False, "更新失败：新的材料名称与其他现有材料冲突"

    # --- 3. 删除 ---
    @classmethod
    async def delete_material(cls, material_id: int):
        try:
            material_obj = await async_db.get(cls, id=material_id)
            await async_db.delete(material_obj)
            return True, "材料删除成功"
        except DoesNotExist:
            return False, f"未找到 ID 为 {material_id} 的材料"

    # --- 4. 分页查询 ---
    @classmethod
    async def filter_materials_with_pagination(cls, name: str = None, software: str = None, page: int = 1, page_size: int = 10):
        query = cls.select()
        filters = []
        
        if name: filters.append(cls.name.contains(name))
        if software: filters.append(cls.source_software == software)
            
        if filters:
            query = query.where(*filters)
            
        total_count = await async_db.count(query)
        query = query.order_by(cls.id.desc()).paginate(page, page_size)
        results = await async_db.execute(query)
        
        return results, total_count