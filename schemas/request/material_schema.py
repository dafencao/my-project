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
