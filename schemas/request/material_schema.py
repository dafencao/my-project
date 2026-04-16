from typing import Optional,Dict,Any,List
from pydantic import BaseModel, Field,validator
from decimal import Decimal

TemperatureCurve = List[List[float]]


class MaterialProperties(BaseModel):
    """
    定义已知的、必须对齐格式的材料属性。
    所有这些属性如果存在，都必须严格遵守 TemperatureCurve (二维数组) 格式。
    """
    mk: Optional[TemperatureCurve] = Field(default=None, description="导热系数曲线 [[T, value], ...]")
    mRho: Optional[TemperatureCurve] = Field(default=None, description="密度曲线 [[T, value], ...]")
    mAl: Optional[TemperatureCurve] = Field(default=None, description="热膨胀系数曲线")
    mNu: Optional[TemperatureCurve] = Field(default=None, description="泊松比曲线")
    mCp: Optional[TemperatureCurve] = Field(default=None, description="比热容曲线")
    mYld: Optional[TemperatureCurve] = Field(default=None, description="屈服强度曲线")
    mE: Optional[TemperatureCurve] = Field(default=None, description="弹性模量曲线")

    # [可选] 自定义校验器：确保每一行数据真的是只有两个值 [温度, 数值]
    @validator('*', pre=False) # * 表示应用到所有字段
    def check_curve_shape(cls, v, field):
        if v is not None:
            for point in v:
                if len(point) != 2:
                    raise ValueError(f"参数 {field.name} 的数据点 {point} 格式错误，必须为 [温度, 数值]")
        return v

    class Config:
        # 关键配置：允许录入未在上面定义的额外字段！
        # 这样既保证了已知字段格式严谨，又保留了未来新增未知参数的灵活性
        extra = "allow" 

# ==========================================
# 2. 修改原来的接收入口模型
# ==========================================
class MaterialBase(BaseModel):
    name: str = Field(..., max_length=100, description="材料名称，如：2060铝锂合金")
    source_software: Optional[str] = Field(default="jmatpro", max_length=50)
    description: Optional[str] = Field(default=None, description="材料详细描述")
    properties: MaterialProperties = Field(
        default_factory=MaterialProperties, 
        description="材料物性库"
    )

    class Config:
        # Pydantic v1 的写法 (如果你的 FastAPI 比较旧，用这个)
        schema_extra = {
            "example": {
                "name": "2060铝锂合金",
                "source_software": "Marc(mm-tonne-s)",
                "description": "这是一个测试材料，展示标准的二维数组格式",
                "properties": {
                    "mk": [
                        [20.0, 150.5],
                        [100.0, 155.2]
                    ],
                    "mRho": [
                        [20.0, 2.6e-09],
                        [500.0, 2.5e-09]
                    ]
                }
            }
        }

class MaterialBase(BaseModel):
    """材料公共基础字段 (不包含 properties)"""
    name: str = Field(..., max_length=100, description="材料名称，如：2060铝锂合金")
    source_software: Optional[str] = Field(default="Marc(mm-tonne-s)", max_length=50, description="数据来源软件")
    description: Optional[str] = Field(default=None, description="材料详细描述")

class MaterialCreate(MaterialBase):
    """【新增】接口请求体 POST /material/add"""
    # 继承了 name (必填), source_software, description
    properties: MaterialProperties = Field(
        None, 
        description="材料物性库"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "2060铝锂合金",
                "source_software": "Marc(mm-tonne-s)",
                "description": "用于数字孪生系统的高温物性参数表",
                "properties": {
                    "mk": [[20.0, 150.5], [100.0, 155.2]]
                }
            }
        }

class MaterialUpdate(BaseModel):
    """【更新】接口请求体 PUT /material/{id}"""
    # 更新时所有字段都应是 Optional (选填)，传什么就更新什么
    name: Optional[str] = Field(None, max_length=100, description="材料名称")
    source_software: Optional[str] = Field(None, max_length=50, description="数据来源软件")
    description: Optional[str] = Field(None, description="材料详细描述")
    properties: Optional[MaterialProperties] = Field(None, description="需要更新或追加的物性库")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "修正了部分高温下的参数描述",
                "properties": {
                    "mCp": [[20.0, 8.5e5], [500.0, 9.2e5]]
                }
            }
        }

class MaterialQuery(BaseModel):
    """【查询】接口请求体 (Query Params) GET /material/search"""
    # GET 请求通过 url 传参，通常包含分页和模糊查询条件
    name: Optional[str] = Field(None, description="按名称模糊搜索")
    source_software: Optional[str] = Field(None, description="按来源软件筛选")
    
    current: int = Field(1, description="页码", ge=1)
    pageSize: int = Field(10, description="每页条数", gt=0)
