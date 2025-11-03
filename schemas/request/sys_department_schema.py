from datetime import datetime
import re
from typing import List, Optional

from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field, constr, validator

from utils.tools_func import tz


# SQLAlchemy 模型使用 定义属性，并将类型作为参数传递,   =Column
# 而 Pydantic 模型使用 、 新类型注释语法/类型提示声明类型：

# 用于读取的 Pydantic 模型中，添加一个内部类。ItemUserConfig
# Config类用于为 Pydantic 提供配置

# Shared properties


class DepartmentBase(BaseModel):
    # id: int 自增字段

    dept_id: Optional[int]=0
    parent_id: Optional[int] = Field(
        None, 
        description="父部门ID(顶级部门传 null 或不传)"
    )
    dept_name: Optional[str] = Field(
        None,
        description="部门名称(最长20字符,可选)"
    )
    leader: Optional[str] = Field(
        None,
        max_length=20,
        description="负责人(最长20字符,可选)"
    )
    phone: Optional[str] = Field(
        None,
        max_length=11,
        pattern=r'^1[3-9]\d{9}$',  # 手机号正则校验（可选）
        description="联系电话(手机号格式最长11字符可选)"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="邮箱(合法格式最长50字符可选)"
    )
    status: str = Field(
        '0',  # 默认值：正常
        max_length=1,
        pattern=r'^[01]$',  # 仅允许 0（正常）/1（禁用）
        description="部门状态(0=正常1=禁用默认0)"
    )
    # name: Optional[str] = ''
    # code: Optional[str] = ''
    # sort:Optional[int]
    create_time: Optional[datetime] = None
    
class DepartmentUpdate(BaseModel):
    dept_id: Optional[int] = None
    parent_id: Optional[int] = Field(
        None, 
        description="父部门ID(顶级部门传 null 或不传)"
    )
    dept_name: Optional[str] = Field(
        None,
        description="部门名称(最长20字符,可选)"
    )
    leader: Optional[str] = Field(
        None,
        max_length=20,
        description="负责人(最长20字符,可选)"
    )
    phone: Optional[str] = Field(
        None,
        max_length=11,
        pattern=r'^1[3-9]\d{9}$',  # 手机号正则校验（可选）
        description="联系电话(手机号格式最长11字符可选)"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="邮箱(合法格式最长50字符可选)"
    )
    status: str = Field(
        '0',  # 默认值：正常
        max_length=1,
        pattern=r'^[01]$',  # 仅允许 0（正常）/1（禁用）
        description="部门状态(0=正常1=禁用默认0)"
    )
    update_time: Optional[datetime] = None

class DepartmentQuery(BaseModel):
    code: Optional[str] = ''
    name: Optional[str] = ''
    # current: int= 1
    # pageSize: int = 5
class DepartmentDelete(BaseModel):
    id: Optional[int]
