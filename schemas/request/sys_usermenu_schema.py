'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:07:18
LastEditors: Please set LastEditors
LastEditTime: 2023-05-23 15:18:50
'''
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field
from typing import Optional
from datetime import datetime
import pytz

from utils.tools_func import tz

"""
管理员表的 字段model模型 验证 响应(没写)等
Pydantic 模型
"""


# SQLAlchemy 模型使用 定义属性，并将类型作为参数传递,   =Column
# 而 Pydantic 模型使用 、 新类型注释语法/类型提示声明类型：

# 用于读取的 Pydantic 模型中，添加一个内部类。ItemUserConfig
# Config类用于为 Pydantic 提供配置

# Shared properties


# 菜单基本信息 类名大写！


class MenuBase(BaseModel):
    # id:Optional[int] = "" #add时id一般为自增唯一字段不需要前端传
    menu_name: str = Field(..., max_length=50, description="菜单名称（必填）")
    parent_id: Optional[int] = Field(None, description="父菜单ID(为空表示一级菜单)")
    order_num: int = Field(..., description="显示顺序（必填）")
    path: Optional[str] = Field(None, max_length=200, description="路由地址")
    component: Optional[str] = Field(None, max_length=255, description="组件路径")
    query: Optional[str] = Field(None, max_length=255, description="路由参数")
    is_cache: int = Field(0, ge=0, le=1, description="是否缓存(0-不缓存,1-缓存,默认0)")
    menu_type: str = Field(..., pattern=r'^[MCF]$', description="菜单类型M(-目录,C-菜单,F-按钮)")
    visible: str = Field("0", pattern=r'^[01]$', description="菜单状态(0-显示,1-隐藏,默认0)")
    status: str = Field("0", pattern=r'^[01]$', description="状态(0-正常,1-禁用,默认0)")
    perms: Optional[str] = Field(None, max_length=100, description="权限标识(如 sys:menu:add)")
    icon: Optional[str] = Field(None, max_length=100, description="菜单图标")
    # create_at:Optional[str] = ""#add时create_at一般为后端更新字段 不需要前端传


class usermenuQuery(MenuBase):

    pageNo: str  # 页码
    pageSize: str  # 每页条数


# TODO: 新增菜单接口接收参数如下 写新增菜单接口
class MenuCreate(MenuBase):
    create_at:datetime = None




class MenuUpdate(BaseModel):
    id: Optional[int]
    parent_id: Optional[str] = None
    menuType: Optional[int]
    name: Optional[str]
    url: Optional[str]
    component: Optional[str]

    sortNo: Optional[int]
    icon: Optional[str] = None

    updateAt: Optional[datetime] =None

    # description: Optional[str] = ''


class MenuQuery(MenuBase):
    # query继承MenuBase基本信息的查询参数
    sortNo: int = None
    menuType: int = None

    # 还可以定义额外的查询参数
    name: Optional[str] = ""
    current: int = 1  # 页码
    pageSize: int = 5  # 每页条数


# 创建 Pydantic 模型（模式），这些模型将在读取数据时从 API 返回数据时使用
