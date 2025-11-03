"""
纯增删改查操作,写在model里面
"""

from common.session import BaseModel, paginator, db, async_db
from peewee import CharField, IntegerField, BigAutoField,BigIntegerField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from peewee import fn, JOIN
import time
from utils.tools_func import convert_arr, convert_num_arr


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
        u = await async_db.execute(Department.update(**department).where(Department.dept_id == department['id']))
        #
        return u

    @classmethod
    async def fuzzy_query(cls, querydepartment):
        db = await async_db.execute(Department.select().where(Department.code.contains(querydepartment['code']),
                                       Department.name.contains(querydepartment['name'])).order_by(
            Department.sort,Department.code ).dicts())
        result = list(db)
        return result
    # Department.name == querydepartment['name']
    @classmethod
    async def select_all(cls):  # 获取
        db = await async_db.execute(Department.select().dicts())
        # 附加 iterator() 方法调用还可以减少内存消耗
        return list(db)
