'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:07:18
LastEditors: Please set LastEditors
LastEditTime: 2023-04-23 16:10:05
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
class FanBase(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = ''
    label: Optional[str] = ''
    description: Optional[str] = ''
    img: Optional[str] = ''  # 风机图片路径
    train_type: Optional[int] = ''  # 风机所属车辆类型
    remark: Optional[str] = ''  # 预留字段
    create_by: Optional[str] = ''  # 创建用户
    create_at: Optional[str] = ''  # 创建用户
    update_by: Optional[str] = ''  # 更新用户
    update_at: Optional[str] = ''  # 更新用户
    label_description: Optional[str] = ''
    sheet: Optional[str] = ''


class FanQuery(BaseModel):
    name: Optional[str] = ""
    label: Optional[str] = ""
    train_type: Optional[int] = ""
    current: int = 1  # 页码
    pageSize: int = 10  # 每页条数


class FanDelete(BaseModel):
    id: Optional[int]


# # 创建风机信息需要验证的条件
class FanCreate(BaseModel):
    name: Optional[str]
    label: Optional[str]
    coolObject: Optional[str]
    description: Optional[str]
    img: Optional[str]
    train_type: Optional[int]
    remark: Optional[str]
    create_by: Optional[str]
    create_at: Optional[datetime] = None


class FanUpdate(BaseModel):
    id: Optional[int]
    # id: str
    name: Optional[str]
    label: Optional[str]
    coolObject: Optional[str]
    description: Optional[str]
    img: Optional[str]
    train_type: Optional[int]
    remark: Optional[str]
    update_by: Optional[str]
    label_description: Optional[str]
    sheet: Optional[str]
    show: Optional[str]
    update_at: Optional[datetime] = None
