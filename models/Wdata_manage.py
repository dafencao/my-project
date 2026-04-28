from peewee import AutoField, CharField, DecimalField, TextField, IntegerField, DateTimeField, BooleanField, DoesNotExist
from common.session import BaseModel, paginator, db, async_db
from playhouse.mysql_ext import JSONField
from peewee import DoesNotExist

class WProcessRecord(BaseModel):
    id = AutoField(primary_key=True)
    record_name = CharField(max_length=100)
    dataset_type = CharField(max_length=20, default='unassigned')
    batch_tag = CharField(max_length=50, null=True)
    file_path = CharField(max_length=255)
    
    material_id = IntegerField()
    joint_id = IntegerField()
    method_id = IntegerField()
    
    welding_speed = DecimalField(max_digits=8, decimal_places=2, null=True)
    heat_input = DecimalField(max_digits=10, decimal_places=2, null=True)
    parameters = JSONField() 
    
    is_locked = BooleanField(default=False)
    description = TextField(null=True)
    
    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)

    class Meta:
        table_name = 'welding_process_records'

    # --- 1. 新增 ---
    @classmethod
    async def add_record(cls, data: dict):
        result = await async_db.create(cls, **data)
        return True, result.id, "工艺实验记录添加成功"

    # --- 2. 删除 ---
    @classmethod
    async def delete_record(cls, record_id: int):
        try:
            obj = await async_db.get(cls, id=record_id)
            if obj.is_locked:
                return False, "该数据已被锁定（用于训练），禁止删除"
            await async_db.delete(obj)
            return True, "记录删除成功"
        except DoesNotExist:
            return False, "未找到该记录"

    # --- 3. 更新 ---
    @classmethod
    async def update_record(cls, record_id: int, update_data: dict):
        try:
            obj = await async_db.get(cls, id=record_id)
            if obj.is_locked and update_data.get("is_locked") is not False:
                # 除非这次更新是为了解锁，否则锁定状态下禁止修改其他参数
                return False, "数据已锁定，请先解除锁定后再修改参数"
                
            for key, value in update_data.items():
                setattr(obj, key, value)
            await async_db.update(obj)
            return True, "记录更新成功"
        except DoesNotExist:
            return False, "未找到该记录"

    # --- 4. 后台分页查询 ---
    @classmethod
    async def filter_records(cls, name=None, dataset=None, batch=None, m_id=None, page=1, page_size=10):
        query = cls.select()
        filters = []
        if name: filters.append(cls.record_name.contains(name))
        if dataset: filters.append(cls.dataset_type == dataset)
        if batch: filters.append(cls.batch_tag == batch)
        if m_id: filters.append(cls.material_id == m_id)
            
        if filters: query = query.where(*filters)
            
        total = await async_db.count(query)
        query = query.order_by(cls.id.desc()).paginate(page, page_size)
        results = await async_db.execute(query)
        return results, total

    # --- 5. 专供深度学习模型的检索接口 ---
    @classmethod
    async def get_dataset_for_ml(cls, dataset_type: str, batch_tag: str = None):
        """只返回模型需要的核心数据：ID、路径、通用特征、JSON参数"""
        query = cls.select().where(cls.dataset_type == dataset_type)
        if batch_tag:
            query = query.where(cls.batch_tag == batch_tag)
            
        # 强制按照 ID 升序，保证模型每次拉取数据的顺序完全一致（复现性要求）
        results = await async_db.execute(query.order_by(cls.id.asc()))
        return results