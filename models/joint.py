from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, CharField, TextField, Model, AutoField,IntegerField, DecimalField, DateTimeField,IntegrityError
from playhouse.mysql_ext import JSONField
from peewee import DoesNotExist
import datetime


class WeldingJoint(BaseModel):
    id = AutoField(primary_key=True, help_text="主键ID")
    joint_code = CharField(max_length=50, unique=True, help_text="接头编号或名称")
    joint_type = CharField(max_length=50, help_text="接头形式 (对接, T型接头等)")
    groove_type = CharField(max_length=50, help_text="焊接坡口 (不开, 单侧, 双侧等)")
    
    # max_digits=8 表示总位数为8，decimal_places=2 表示保留2位小数
    t1_thickness = DecimalField(max_digits=8, decimal_places=2, help_text="t1工件板厚(mm)")
    t2_thickness = DecimalField(max_digits=8, decimal_places=2, help_text="t2工件板厚(mm)")
    
    weld_layers = IntegerField(default=1, help_text="焊层数量")
    welding_gap = DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="焊接间隙(mm)")
    
    description = TextField(null=True, help_text="备注信息")
    
    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)

    class Meta:
        table_name = 'welding_joints'
    class Config:
        orm_mode = True 

    @classmethod
    async def add_joint(cls, joint_data: dict):
        """异步添加接头信息 (如果编号冲突则拦截)"""
        try:
            result = await async_db.create(cls, **joint_data)
            return True, result.id, "接头添加成功"
        except IntegrityError:
            return False, None, f"接头编号 '{joint_data.get('joint_code')}' 已存在，请勿重复录入"
    

    # --- 删 ---
    @classmethod
    async def delete_joint(cls, joint_id: int):
        try:
            joint_obj = await async_db.get(cls, id=joint_id)
            await async_db.delete(joint_obj)
            return True, "接头删除成功"
        except DoesNotExist:
            return False, f"未找到 ID 为 {joint_id} 的接头数据"

    # --- 改 ---
    @classmethod
    async def update_joint(cls, joint_id: int, update_data: dict):
        try:
            joint_obj = await async_db.get(cls, id=joint_id)
            
            # 动态赋予新值
            for key, value in update_data.items():
                setattr(joint_obj, key, value)
                
            await async_db.update(joint_obj)
            return True, "接头更新成功"
        except DoesNotExist:
            return False, f"未找到 ID 为 {joint_id} 的接头数据"
        except IntegrityError:
            return False, "更新失败：该接头编号已存在，请更换"

    # --- 查 (全部) ---
    @classmethod
    async def get_all_joints(cls):
        """获取全表数据 (倒序)"""
        query = cls.select().order_by(cls.id.desc())
        return await async_db.execute(query)

    # --- 查 (条件筛选 + 分页) ---
    @classmethod
    async def filter_joints(cls, code: str = None, j_type: str = None, page: int = 1, page_size: int = 10):
        query = cls.select()
        filters = []
        
        # 组装条件
        if code:
            filters.append(cls.joint_code.contains(code)) # 模糊匹配
        if j_type:
            filters.append(cls.joint_type == j_type)      # 精确匹配
            
        if filters:
            query = query.where(*filters)
            
        # 统计总数并执行分页查询
        total_count = await async_db.count(query)
        query = query.order_by(cls.id.desc()).paginate(page, page_size)
        results = await async_db.execute(query)
        
        return results, total_count