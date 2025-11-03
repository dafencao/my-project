'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:07:18
LastEditors: Please set LastEditors
LastEditTime: 2023-05-07 16:51:39
'''
import pytz

from utils.tools_func import tz

"""
管理员表的 字段model模型 验证 响应(没写)等
Pydantic 模型
"""




from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field
class userroleBase(BaseModel):
    id: Optional[str] = ''
    # roleCode : Optional[EmailStr] = ''
    roleCode: Optional[str] = ''
    roleName: Optional[str] = ''
    updateBy: Optional[str] = ''
    updateTime: Optional[str] = ''
    createBy: Optional[str] = ''
    createTime: Optional[str] = ''
    description: Optional[str] = ''


class userroleQuery(BaseModel):

    roleName: Optional[str] = ''
    roleCode: Optional[str] = ''
    current: int = 1  # 页码
    pageSize: int = 10  # 每页条数


# 创建 Pydantic 模型（模式），这些模型将在读取数据时从 API 返回数据时使用


# # 创建账号需要验证的条件
class UserroleCreate(BaseModel):

    roleCode: str
    createBy: str
    roleName: str
    description: str


class UserroleUpdate(BaseModel):
    id: int
    roleCode: str
    roleName: str
    updateBy: str
    description: str = None
    updateAt: datetime = None


class RoleQuery(userroleQuery):
    current: int = 1
    pageSize: int = 10


class RoleCreate(BaseModel):
    description: Optional[str] = ''
    roleCode: Optional[str]
    roleName: Optional[str]
    createBy:  Optional[str]
    permissionIds: List[int] = []


class RoleUpdate(BaseModel):
    id: Optional[int]
    description: Optional[str] = ''
    roleCode: Optional[str]
    roleName: Optional[str]
    updateBy:  Optional[str]
    updateAt: datetime = None


class RoleMenuPerm(BaseModel):
    lastpermissionIds: List[int]
    permissionIds: List[int]
    roleId: Optional[int]
