'''
Author: 嘉欣 罗 2592734121@qq.com
Date: 2022-12-25 15:32:44
LastEditors: Please set LastEditors
LastEditTime: 2023-05-09 17:15:41
FilePath: \psad-backend\schemas\request\sys_fan_schema.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import pytz

from utils.tools_func import tz

"""
风机表的 字段model模型 验证 响应(没写)等
Pydantic 模型
"""


# SQLAlchemy 模型使用 定义属性，并将类型作为参数传递,   =Column
# 而 Pydantic 模型使用 、 新类型注释语法/类型提示声明类型：

# 用于读取的 Pydantic 模型中，添加一个内部类。ItemUserConfig
# Config类用于为 Pydantic 提供配置

# Shared properties


# @dataclass




from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field, validator
from pydantic.dataclasses import dataclass as pydantic_dataclass
from dataclasses import dataclass
from typing import List, Optional, Type, Union
from fastapi import FastAPI, File, Form, Depends, UploadFile
from  datetime import  datetime
class FanBase(BaseModel):
    # 接收前端参数 加不加别名都可以
    # application_model: Optional[str] = Field('', alias='applicationModel')

    # applicationModelId: Optional[int] = Field('')
    applicationModelId: Optional[str] = Field('')
    applicationModel: Optional[str] = Field('')
    categoryId: Optional[str] = ''
    category: Optional[str] = ''

    coolObject: Optional[str] = Field('')
    model: Optional[str] = ''
    figNum: Optional[str] = ''
    version: Optional[str] = ''
    flowRate: float = Field(None)
    fullPressure: float = Field(None)
    staticPressure: float = Field(None)

    efficiency: float = Field(None)
    shaftPower: float = Field(None)
    impellerDiameter: float = Field(None)

    weight: float = Field(None)

    motoModel: Optional[str] = Field('')
    powerFrequency: float = Field(None)
    motorPower: float = Field(None)
    motorSpeed: float = Field(None)
    ratedVoltage: int = Field(None)
    ratedCurrent: int = Field(None)

    impellerOuterDiameter: float = Field(None)
    impellerInnerDiameter: float = Field(None)
    impellerOutlet: float = Field(None)
    impellerInlet: float = Field(None)
    exitCorner: float = Field(None)
    inletCorner: float = Field(None)
    impellerNumber: int = Field(None)

    remark1: Optional[str] = ''
    remark2: Optional[str] = ''

    altitude: float = Field(None)
    temperature: float = Field(None)

    class Config:
        orm_mode = True

# # 创建 Pydantic 模型（模式），这些模型将在读取数据时从 API 返回数据时使用


class PerfData(BaseModel):
    fullPressure:  float = Field()
    staticPressure: float = Field()
    fanEff: float = Field()
    staticPressureEff: float = Field()
    motorSpeed: float = Field()
    impellerDiameter: float = Field()
    specificSpeed: float = Field()
    u: float = Field()
    flowCoefficient: float = Field()
    pressureCoefficient: float = Field()
    flowRate: float = Field()
    modelId: float = Field()
    noise: float = Field(None)


class CreatePerfData(BaseModel):
    # perfData:{
    #          header:['header'],
    #          dataIndex:['key'],
    #          data:[{'key':'value}]}
    header: List[str]
    dataIndex: List[str]
    data: List[PerfData]


class FanAdd(FanBase):
    # applicationModel: Optional[str] = ''
    # category: Optional[str] = ''

    # coolObject: Optional[str] =''
    # model: Optional[str] = ''
    # flowRate: float = Field(None, alias='flowRate')
    # fullPressure: float = Field(None, alias='fullPressure')
    # staticPressure: float = Field(None, alias='staticPressure')

    # efficiency: float = Field(None, alias='efficiency')
    # shaftPower: float = Field(None, alias='shaftPower')
    # impellerDiameter: float = Field(None, alias='impellerDiameter')

    # weight: float = Field(None, alias='weight')
    # motorSpeed: Optional[float] = Field(None)
    # # motorSpeed: Optional[float]
    # motorModel: Optional[str] = Field(None)

    # ratedVoltage: int = Field(None)
    # ratedCurrent: int = Field(None)

    # remark1: Optional[str] = Field('')
    # remark2: Optional[str] = Field('')

    # altitude: float = Field(None)
    # temperature: float = Field(None)
    header: list = []
    dataIndex: str = ''
    # data: Optional[str] = Field(None)
    # img_Outline: Optional[File] = Field(None)
    # img3d: Optional[File] = Field(None)
    # technicalFile: Optional[str] = Field('')

    class Config:
        orm_mode = True
class img3d(BaseModel):
    img3d:List[Union[UploadFile, str]]

class FanQuery(FanBase):
    current: int = 1
    pageSize: int = 10
    # 选型参数：
    # x y 参数
    sortParam1: Optional[str] = Field(None)
    sortParam2: Optional[str] = Field(None)

    sort: Optional[bool] = Field(None)
    # sort[0]=true  x = sortParam1 y = sortParam2
    # sort[0]=false y = sortParam1 x = sortParam2

    # 5% 10%
    # sortRange: Optional[str] = Field(None)
    sortRange: Optional[list] = Field(None)

    # 相似设计参数：
    sortField: Optional[str] = Field(None)
    sortOrder: Optional[str] = Field(None)

    # 范围查询参数：
    flowRateBetween: List[float] = Field(None)
    fullPressureBetween: List[float] = Field(None)
    motorSpeedBetween: List[float] = Field(None)
    shaftPowerBetween: List[float] = Field(None)
    efficiencyBetween: List[float] = Field(None)

    status: str = Field(None)
    manage: Optional[bool] = Field(False)
    createBy: Optional[str] = Field(None)

    # 产品介绍按型号排序
    sortedByModel: Optional[bool] = Field(None)
    # @validator('proportion', pre=True)
    # def blank_string(value, field):
    #     if value == "":
    #         return None
    #     return value


class FanSimilarQuery(FanBase):
    current: int = 1
    pageSize: int = 10
    # 相似设计参数：
    # 流量
    sortFlowRate: float = Field(None)
    # 全压
    sortFullPressure: float = Field(None)
    # 静压
    sortStaticPressure: float = Field(None)
    pressureField: str = Field(None)
    # 转速
    sortMotorSpeed: float = Field(None)
    # 比转速
    specificSpeed: float = Field(None)
    # 叶轮直径范围
    impellerDiameterMin: float = Field(None)
    impellerDiameterMax: float = Field(None)
    impellerDiameterRatioMax: float = Field(None)
    impellerDiameterRatioMin: float = Field(None)

    sortFields: List[str] = Field([])
    # 排序参数
    sortOrder: Optional[str] = Field(None)

    # 限定
    # limitCategory: List[List[str]] = Field(None)
    limitCategoryId: List[str] = Field(None)
    limitField:  Optional[str] = Field(
        None, title='title', description="The price must be greater than zero")
    min:  Optional[int] = Field(None)
    max:  Optional[int] = Field(None)

class FanChangeQuery(FanBase):
    current: int = 1
    pageSize: int = 10
 # 变形设计参数：
    # 流量
    sortFlowRate: float = Field(None)
    # 全压
    sortFullPressure: float = Field(None)
    # 静压
    sortStaticPressure: float = Field(None)
    pressureField: str = Field(None)
    # 转速
    sortMotorSpeed: float = Field(None)
    # 比转速
    specificSpeed: float = Field(None)
    # # 叶轮直径范围
    impellerDiameterMin: float = Field(None)
    impellerDiameterMax: float = Field(None)
    impellerDiameterRatioMax: float = Field(None)
    impellerDiameterRatioMin: float = Field(None)

    sortFields: List[str] = Field([])
    # 排序参数
    sortOrder: Optional[str] = Field(None)

    # 限定
    # limitCategory: List[List[str]] = Field(None)
    limitCategoryId: List[str] = Field(None)
    limitField:  Optional[str] = Field(
        None, title='title', description="The price must be greater than zero")
    min:  Optional[int] = Field(None)
    max:  Optional[int] = Field(None)

class FanAudit(BaseModel):
    auditBizId: Optional[str] = Field(None)
    userId:Optional[str] = Field(None)
    result:Optional[str] = Field(None)
    remark:Optional[str] = Field(None)
    # auditType:Optional[str] = Field('fanAddAudit')
class queryAuditRecord(BaseModel):
    auditBizId: Optional[str]
    auditType:Optional[str]

class ExcelDataBase(BaseModel):

    header: Optional[list] = Field(None)
    dataIndex: Optional[list] = Field(None)
    data: Optional[list] = Field(None)

class ApplModelCreate(BaseModel):
    code:str
    name:str
    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None
class ApplModelUpdate(BaseModel):
    id:int
    code:str
    name:str
    updateAt: Optional[datetime] = None



class CategoryBase(BaseModel):
    # id: int 自增字段

    parentId: Optional[int] = 0
    name: Optional[str] = ''
    # series: Optional[str] = ''
    sort: Optional[int]
    code:Optional[str]
    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None


class CategoryUpdate(BaseModel):
    id: Optional[int]
    parentId: Optional[int] = 0
    name: Optional[str]
    # series: Optional[str] = ''
    code:Optional[str]
    sort: Optional[int] = 1
    updateAt: Optional[datetime] = None


class CategoryQuery(BaseModel):
    series: Optional[str] = ''
    name: Optional[str] = ''
    # current: int= 1
    # pageSize: int = 5


class CategoryDelete(BaseModel):
    id: Optional[int]