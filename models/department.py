"""
纯增删改查操作,写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, BigAutoField,BigIntegerField,DateTimeField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from peewee import fn, SQL
import time
from utils.tools_func import convert_arr, convert_num_arr
from datetime import datetime
import pytz


class Department(BaseModel):
    """
    部门表，
    """
    # 部门ID：自增主键（bigint类型）
    dept_id = BigAutoField(primary_key=True, verbose_name="部门ID")
    # 父部门ID：允许为 NULL（表示顶级部门）
    parent_id = BigIntegerField(null=True, verbose_name="父部门ID")
    # 部门名称：非空，最长30字符
    dept_name = CharField(max_length=30, null=False, verbose_name="部门名称")
    # 负责人：最长20字符，可为空
    leader = CharField(max_length=20, null=True, verbose_name="负责人")
    # 联系电话：最长11字符（如手机号），可为空
    phone = CharField(max_length=11, null=True, verbose_name="联系电话")
    # 邮箱：最长50字符，可为空
    email = CharField(max_length=50, null=True, verbose_name="邮箱")
    # 部门状态：char(1)，通常用 '0' 表示正常，'1' 表示禁用（非空）
    status = CharField(max_length=1, null=False, default='0', verbose_name="部门状态")
    # 删除标志：char(1)，'0' 表示未删除，'1' 表示已删除（非空）
    del_flag = CharField(max_length=1, null=False, default='0', verbose_name="删除标志")
    # create_at = DateTimeField(default=datetime.now(pytz.timezone('Asia/Shanghai')), verbose_name="创建时间")
    # update_at = DateTimeField(default=datetime.now(pytz.timezone('Asia/Shanghai')), verbose_name="创建时间")


    class Meta:
        table_name = 'sys_dept'  # 自定义映射的表名
        verbose_name = "部门信息表"

    class Config:
        orm_mode = True

    @classmethod
    async def add_department(cls, department):  # 添加部门
        # result = await async_db.execute(Department.create(**department))
        result = await async_db.create(Department,**department)
        return result.id

    @classmethod
    async def del_by_department_id(cls, id):
        await async_db.execute(Department.delete().where(Department.dept_id == id))

    @classmethod
    async def update_department(cls, department):
        # 字典结构更新数据
        print(department)
        u = await async_db.execute(Department.update(**department).where(Department.dept_id == department['dept_id']))
        #
        return u

    @classmethod
    async def fuzzy_query(cls, querydepartment):
        # 构建查询条件
        conditions = []
        
        # 对于数字字段使用精确匹配
        if 'dept_id' in querydepartment and querydepartment['dept_id'] is not None:
            conditions.append(Department.dept_id == querydepartment['dept_id'])
        
        if 'parent_id' in querydepartment and querydepartment['parent_id'] is not None:
            conditions.append(Department.parent_id == querydepartment['parent_id'])
    
        # 执行查询
        if conditions:
            db = await async_db.execute(
                Department.select()
                .where(*conditions)
                .order_by(Department.parent_id, Department.dept_id)
                .dicts()
            )
        else:
            # 如果没有条件，返回所有数据
            db = await async_db.execute(
                Department.select()
                .order_by(Department.parent_id, Department.dept_id)
                .dicts()
            )
        
        result = list(db)
        return result

    @classmethod
    async def select_all(cls):  # 获取所有部门
        # 优化：添加排序（与模糊查询保持一致），避免返回顺序混乱
        query = cls.select().order_by(cls.parent_id, cls.dept_id).dicts()
        db_result = await async_db.execute(query)
        return list(db_result)
    
 