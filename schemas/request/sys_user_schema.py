
"""
管理员表的 字段model模型 验证 响应(没写)等
Pydantic 模型
"""

from datetime import datetime, date
import re
from typing import List, Optional, Union

import pytz
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field, constr, validator

from utils.tools_func import tz


# SQLAlchemy 模型使用 定义属性，并将类型作为参数传递,   =Column
# 而 Pydantic 模型使用 、 新类型注释语法/类型提示声明类型：

# 用于读取的 Pydantic 模型中，添加一个内部类。ItemUserConfig
# Config类用于为 Pydantic 提供配置

# Shared properties


class UserBase(BaseModel):
    # id: str

    account:  Optional[str]
    email: Optional[EmailStr] = None
    realName: Optional[str] = ''
    sex: Optional[str] = ''
    phone: Optional[str] = ''
    oraCode: Optional[int] = None
    jobAge: Optional[str] = ''
    level: Optional[int] = ''
    userRoleId: Optional[int] = None
    birthday: Optional[datetime] = None


# class UserQuery(UserBase):
#     current: int = 1
#     pageSize: int = 10
#     account: Optional[str] = ''
#     role: int = Field(None)

class UserQuery(BaseModel):
    # id: Optional[str] = ""
    # account: Optional[str] = ""
    account: Optional[str] = None
    realName: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    userRole: Optional[str] = None
    sex: Optional[str] = None

    current: int = 1  # 页码
    pageSize: int = 5  # 每页条数

# 创建账号需要验证的条件


class UserCreate(BaseModel):

    account:  Optional[str]
    password: Optional[str]
    realName: Optional[str]
    userRoleId: Optional[int]
    sex: Optional[str] = ''

    email: Optional[EmailStr] = ''
    # phone: Optional[str] = ''
    phone: Optional[constr(min_length=11, max_length=11)] = ''

    oraCode: Optional[int]
    level: Optional[str]
    jobAge: Optional[float]=0

    birthday: Optional[Union[date, datetime]]
    post: List[int] = None
    line: List[int] = None
    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None

    @validator('phone')
    def is_phone(cls, tel):
        ret = re.match(r"^1[345678]\d{9}$", tel)
        if ret:
            return ret.group()
        else:
            print("匹配失败")
            raise ValueError('手机号不正确')
    # # account: Optional[str] = ''
    # role: int = Field(None)
    # # authority_id: int = 1
    # avatar: Optional[AnyHttpUrl] = None

# Properties to receive via API on update

# 创建账号需要验证的条件


class UsersCreate(BaseModel):

    account:  Optional[str]
    password: Optional[str]
    realName: Optional[str]
    userRoleId: Optional[int] = None
    roleCode: Optional[str]
    sex: Optional[str] = ''

    # email: Optional[str] = ''
    email: Optional[EmailStr] = ''
    phone: Optional[constr(min_length=11, max_length=11)]
    oraCode: Optional[int] = None
    department: Optional[str]  # =None
    level: Optional[str]
    jobAge: Optional[str]

    birthday: Union[datetime,date] = None
    post: List[str] = None
    line: List[str] = None
    createAt: Optional[datetime] = None

    @validator('phone')
    def is_phone(cls, tel):
        ret = re.match(r"^1[35678]\d{9}$", tel)
        if ret:
            return ret.group()
        else:
            print("匹配失败")
            raise ValueError('手机号不正确')

    # # account: Optional[str] = ''
    # role: int = Field(None)
    # # authority_id: int = 1
    # avatar: Optional[AnyHttpUrl] = None


class UserUpdate(UserBase):
    id: str
    # password: Optional[str] = None
    updateAt: Optional[datetime] = None
    line: List[int]=None
    post: List[int]=None
    email: Optional[EmailStr]  = None

    # lastUserInfo: Optional[str]

    pass
# 创建 Pydantic 模型（模式），这些模型将在读取数据时从 API 返回数据时使用


class UserUpdatePwd(BaseModel):
    id: Optional[str]
    account: Optional[str]
    oldPassword: Optional[str] = None  # 管理员修改用户密码时不需要旧密码
    password: Optional[str]
    updateAt: Optional[datetime] = datetime.now(pytz.timezone('Asia/Shanghai'))


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
class UserInfo(BaseModel):
    role_id: int
    role: str
    nickname: str
    avatar: AnyHttpUrl


class UserAuth(BaseModel):
    account: str
    password: str
# 邮箱登录认证 验证数据字段都叫account


class UserEmailAuth(UserAuth):
    account: EmailStr


# 手机号登录认证 验证数据字段都叫account
class UserPhoneAuth(UserAuth):
    account: str
