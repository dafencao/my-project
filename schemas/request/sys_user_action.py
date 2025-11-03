'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:07:18
LastEditors: Please set LastEditors
LastEditTime: 2023-05-05 10:23:55
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
class UseractionBase(BaseModel):
    id: Optional[int] = None
    username: Optional[str] = ''
    userRealName: Optional[str] = ''
    actionTime: Optional[str] = ''
    actionName: Optional[str] = ''
    actionId: Optional[str] = ''
    actionType: Optional[str] = ''  # 风机所属车辆类型
    actionModel: Optional[str] = ''
    monitorModule: Optional[str] = ''
    pageUrl: Optional[str] = ''  # 预留字段
    pageName: Optional[str] = ''  # 创建用户
    pageArea: Optional[str] = ''  # 创建用户
    description: Optional[str] = ''  # 更新用户
    remark: Optional[str] = ''  # 更新用户


class UseractionQuery(BaseModel):
    username: Optional[str] = ""
    userRealName: Optional[str] = ''
    updateAt: List[datetime] = None
    beginTime: Optional[str] = ""
    endTime: Optional[str] = ""
    current: int = 1  # 页码
    pageNo: int = 1  # 页码
    pageSize: int = 10  # 每页条数

# class FanDelete(BaseModel):
#     id: Optional[int]

class testCreate(BaseModel):
    updateAt:  Optional[datetime] = datetime.now(pytz.timezone('Asia/Shanghai'))

# # 创建风机信息需要验证的条件
class UseractionCreate(BaseModel):
    updateAt:  Optional[datetime] = None
    actionName: Optional[str]
    actionId: Optional[str]
    actionType: Optional[str]
    actionModel: Optional[str]
    monitorModule: Optional[str]
    pageUrl: Optional[str]
    pageName: Optional[str]
    pageArea: Optional[str]   # 创建用户
    description: Optional[str]
    remark: Optional[str]
    username: Optional[str]
    userRealName: Optional[str] = ''
    ip: Optional[str]


