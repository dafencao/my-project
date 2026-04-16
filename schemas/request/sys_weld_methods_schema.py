from typing import Optional,Dict,Any,List
from pydantic import BaseModel, Field,validator
from decimal import Decimal


class WeldingMethodBase(BaseModel):
    """焊接方法基础字段"""
    method_code: str = Field(..., max_length=50, description="方法代号 (如: GTAW)")
    method_name: str = Field(..., max_length=100, description="方法名称 (如: 钨极氩弧焊/TIG)")
    heat_source: Optional[str] = Field(None, max_length=50, description="热源类型")
    shielding_gas: Optional[str] = Field(None, max_length=50, description="保护方式/气体")
    automation_level: Optional[str] = Field(None, max_length=50, description="自动化程度")
    description: Optional[str] = Field(None, description="工艺特点及适用范围说明")

class WeldingMethodCreate(WeldingMethodBase):
    """【仅新增】POST /method/add 请求体"""
    
    # 保持之前修复 Swagger 显示的写法
    model_config = {
        "json_schema_extra": {
            "example": {
                "method_code": "GTAW",
                "method_name": "钨极惰性气体保护焊 (TIG)",
                "heat_source": "电弧",
                "shielding_gas": "纯氩 (Ar)",
                "automation_level": "手工",
                "description": "电弧燃烧稳定，无飞溅，焊接质量极高。尤其适用于薄板、有色金属打底焊。"
            }
        }
    }

class WeldingMethodUpdate(BaseModel):
    """【仅更新】PUT /method/{id} 请求体"""
    method_code: Optional[str] = Field(None, max_length=50)
    method_name: Optional[str] = Field(None, max_length=100)
    heat_source: Optional[str] = Field(None, max_length=50)
    shielding_gas: Optional[str] = Field(None, max_length=50)
    automation_level: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

class WeldingMethodQuery(BaseModel):
    """【查询】GET /method/search 请求参数"""
    method_code: Optional[str] = Field(None, description="按代号模糊搜索 (如: GT)")
    method_name: Optional[str] = Field(None, description="按名称模糊搜索 (如: 氩弧)")
    current: int = Field(1, ge=1, description="页码")
    pageSize: int = Field(10, gt=0, description="每页条数")