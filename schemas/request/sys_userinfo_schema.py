
"""
管理员表的 字段model模型 验证 响应(没写)等
Pydantic 模型
"""

from typing import Optional

import pytz
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field
import time
from datetime import datetime

from utils.tools_func import tz


# SQLAlchemy 模型使用 定义属性，并将类型作为参数传递,   =Column
# 而 Pydantic 模型使用 、 新类型注释语法/类型提示声明类型：

# 用于读取的 Pydantic 模型中，添加一个内部类。ItemUserConfig
# Config类用于为 Pydantic 提供配置

# Shared properties


class UserBase(BaseModel):
    id: Optional[int] = ""
    email: Optional[EmailStr] = ""
    birthday: Optional[str] = ""
    avatar: Optional[str] = ""
    oracode: Optional[str] = ""
    password: Optional[str] = ""
    phone: Optional[str] = ""
    realName: Optional[str] = ""
    selectedroles: Optional[str] = ""
    sex: Optional[str] = ""
    account: Optional[str] = ""
    level: Optional[str] = ""
    jobage: int


class UserCreate(BaseModel):
    account: Optional[str]
    password: Optional[str]
    realName: Optional[str]
    level: Optional[str]
    jobage: float
    oracode: Optional[str]
    sex: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class userinfoQuery(BaseModel):
    # id: Optional[str] = ""
    # account: Optional[str] = ""
    account: Optional[str] = ""
    realName: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    userRole: Optional[str] = ""
    sex: Optional[str] = ''

    current: int = 1  # 页码
    pageSize: int = 5  # 每页条数


# 创建 Pydantic 模型（模式），这些模型将在读取数据时从 API 返回数据时使用
class UserUpdatePwd(BaseModel):
    id: Optional[str]
    account: Optional[str]
    oldPassword: Optional[str] = None  # 管理员修改用户密码时不需要旧密码
    password: Optional[str]
    updateAt: Optional[datetime] = None


class userinfoAuth(BaseModel):
    account: str
    password: str


# 邮箱登录认证 验证数据字段都叫account
class userinfoEmailAuth(userinfoAuth):
    account: EmailStr


# 手机号登录认证 验证数据字段都叫
class userinfoPhoneAuth(userinfoAuth):
    account: str


# # 创建账号需要验证的条件
# class UserCreate(userinfoBase):
#     account: Optional[str] = ''
#     selectedroles: int = Field(None)
#     password: Optional[str] = None
#     # authority_id: int = 1
#     avatar: Optional[AnyHttpUrl] = None


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None

    # Pydantic会告诉Pydantic模型读取数据，即使它不是，而是一个ORM模型（或任何其他具有属性的任意对象）
    # 不是仅仅尝试从 中获取值，如：username = data["username"]
    # 它还将尝试从属性中获取它：username = data.username

    class Config:
        orm_mode = True


class UserInDB(UserInDBBase):
    hashed_password: str


# 返回的用户信息
# 请注意，读取用户（从 API 返回用户）时将使用的 Pydantic 模型不包括 Userpassword
class userInfo(BaseModel):
    role_id: int
    role: str
    nickname: str
    avatar: AnyHttpUrl


# 修改密码需要验证的条件
class updatePassword(BaseModel):
    account: Optional[str] = ""
    oldpassword: Optional[str] = ""
    password: Optional[str] = ""
    confirmpassword: Optional[str] = ""
