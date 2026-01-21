'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:07:18
LastEditors: Please set LastEditors
LastEditTime: 2023-05-23 15:18:50
'''
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field, validator
from typing import Optional
from datetime import datetime
import pytz
from enum import Enum

from utils.tools_func import tz

"""
管理员表的 字段model模型 验证 响应(没写)等
Pydantic 模型
"""


# SQLAlchemy 模型使用 定义属性,并将类型作为参数传递,   =Column
# 而 Pydantic 模型使用 、 新类型注释语法/类型提示声明类型:

# 用于读取的 Pydantic 模型中,添加一个内部类。ItemUserConfig
# Config类用于为 Pydantic 提供配置

# Shared properties


# 菜单基本信息 类名大写！
class MenuTypeEnum(int, Enum):
    """菜单类型枚举"""
    LEVEL_ONE = 1  # 一级菜单
    SUB_MENU = 2   # 子菜单
    BUTTON = 3     # 按钮(根据业务可能需要)

class BooleanEnum(int, Enum):
    """布尔值枚举(对应tinyint)"""
    FALSE = 0
    TRUE = 1

class StatusEnum(str, Enum):
    """状态枚举"""
    ENABLED = "1"   # 启用
    DISABLED = "0"  # 禁用

class MenuBase(BaseModel):
    # id:Optional[int] = "" #add时id一般为自增唯一字段不需要前端传
    parent_id: Optional[int] = Field(default=None,ge=0,alias="parentId",description="父级菜单ID,NULL表示顶级菜单",example=0)
    menu_name: Optional[str] = Field(default=None,max_length=255,alias="slotTitle",description="菜单名称",example="系统管理")
    menu_type: Optional[int] = Field(default=MenuTypeEnum.LEVEL_ONE,alias="level",description="菜单类型:1-一级菜单,2-子菜单",example=MenuTypeEnum.LEVEL_ONE)
    icon: Optional[str] = Field(default=None,max_length=255,description="菜单图标",example="el-icon-setting")
    description: Optional[str] = Field(default=None,max_length=255,description="菜单描述",example="系统管理菜单")
    componentName: Optional[str] = Field(default=None,max_length=255,description="组件名称",example="SystemManage")
    component: Optional[str] = Field(default=None,max_length=255,description="前端组件路径",example="/system/index")
    permsType: Optional[str] = "1"
    route: Optional[BooleanEnum] = Field(default=BooleanEnum.TRUE,description="是否是路由菜单:0-否,1-是(前端默认为1)",example=BooleanEnum.TRUE)
    sortNo: Optional[int] = Field(default=1,ge=0,description="菜单排序,数字越小越靠前",example=1)
    url: Optional[str] = Field(default=None,max_length=255,alias="path",description="菜单路径(路由路径)",example="/system")
    status: Optional[StatusEnum] = Field(default=StatusEnum.ENABLED,description="状态:1-启用,0-禁用(前端默认为1)",example=StatusEnum.ENABLED)
    keepAlive: Optional[BooleanEnum] = Field(default=BooleanEnum.FALSE,description="是否缓存路由:0-否,1-是(前端默认为0)",example=BooleanEnum.FALSE)
    leaf: Optional[BooleanEnum] = Field(default=BooleanEnum.TRUE,description="是否是叶子节点(0-否,1-是)",example=BooleanEnum.TRUE)
    redirect: Optional[str] = Field(default=None,max_length=255,description="菜单跳转地址",example="/system/user")
    update_at: datetime = None
    create_at:datetime = None


class usermenuQuery(MenuBase):

    pageNo: str  # 页码
    pageSize: str  # 每页条数


# TODO: 新增菜单接口接收参数如下 写新增菜单接口
class MenuCreate(MenuBase):
    create_at:datetime = None




class MenuUpdate(BaseModel):
    menu_id: Optional[int] = Field(default=None,alias='key',description='菜单id')
    parent_id: Optional[int] = Field(default=None,ge=0,alias="parentId",description="父级菜单ID,NULL表示顶级菜单")
    menu_type: Optional[int] = Field(default=MenuTypeEnum.LEVEL_ONE,alias="level",description="菜单类型:1-一级菜单,2-子菜单")
    menu_name: Optional[str] = Field(default=None,max_length=255,alias="slotTitle",description="菜单名称")
    url: Optional[str] = Field(default=None,max_length=255,alias="path",description="菜单路径(路由路径)")
    component: Optional[str] = Field(default=None,max_length=255,description="前端组件路径")
    permsType: Optional[str] = "1" 

    icon: Optional[str] = Field(default=None,max_length=255,description="菜单图标")
    update_at: datetime = None

    # 添加验证器确保必要字段存在
    @validator('menu_id')
    def validate_menu_id(cls, v):
        if not v:
            raise ValueError('菜单ID不能为空')
        return v

    # description: Optional[str] = ''


class MenuQuery(MenuBase):
    # query继承MenuBase基本信息的查询参数
    sortNo: int = None
    menu_type: int = None

    # 还可以定义额外的查询参数
    name: Optional[str] = ""
    current: int = 1  # 页码
    pageSize: int = 5  # 每页条数


# 创建 Pydantic 模型(模式),这些模型将在读取数据时从 API 返回数据时使用
