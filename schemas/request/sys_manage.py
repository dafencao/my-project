"""
管理员表的 字段model模型 验证 响应(没写)等
Pydantic 模型
"""

from datetime import datetime
import re
from typing import List, Optional

import pytz
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field, constr, validator

from utils.tools_func import tz


# 组的创建
class GroupCreate(BaseModel):
    groupId: str
    key: str
    value: str
    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None


class GroupUpdate(BaseModel):
    id: int
    groupId: str
    key: str
    value: str
    updateAt: Optional[datetime] = None


class GroupCompareUpdate(BaseModel):
    last: GroupUpdate
    new: GroupCreate


class GroupDelete(BaseModel):
    groupId: str
    id: int


class GroupQuery(BaseModel):
    # 模糊查询必填字段 str类型应给一个空字符串的默认值，方便模糊查询
    # 模糊查询非必填字段 str类型应给一个None的默认值，sql语句中再做判断
    groupId: List[str] = []
    key: Optional[str] = ''
    value: Optional[str] = ''

    current: int = 1  # 页码
    pageSize: int = 5  # 每页条数
