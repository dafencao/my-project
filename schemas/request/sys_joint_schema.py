from typing import Optional,Dict,Any,List
from pydantic import BaseModel, Field,validator
from decimal import Decimal


class WeldingJointBase(BaseModel):
    joint_code: str = Field(..., max_length=50, description="接头编号，如：WJ-001")
    joint_type: str = Field(..., max_length=50, description="接头形式，例如：对接、T型接头")
    groove_type: str = Field(..., max_length=50, description="焊接坡口，例如：不开、单侧坡口、双侧坡口")
    
    t1_thickness: Decimal = Field(..., ge=0, description="t1工件尺寸/板厚 (mm)")
    t2_thickness: Decimal = Field(..., ge=0, description="t2工件尺寸/板厚 (mm)")
    
    weld_layers: int = Field(default=1, gt=0, description="焊层数量 (至少为1)")
    welding_gap: Decimal = Field(default=Decimal('0.00'), ge=0, description="焊接间隙 (mm)")
    
    description: Optional[str] = Field(default=None, description="接头补充说明")

class WeldingJointCreate(WeldingJointBase):
    """【新增】接头请求体"""
    model_config = {
        "json_schema_extra": {
            "example": {
                "joint_code": "T-JOINT-01",
                "joint_type": "T型接头",
                "groove_type": "单侧坡口",
                "t1_thickness": 12.50,
                "t2_thickness": 10.00,
                "weld_layers": 3,
                "welding_gap": 2.00,
                "description": "主板与腹板采用单面 V 型坡口，打底+填充+盖面共3层"
            }
        }
    }

class WeldingJointUpdate(BaseModel):
    """【仅更新】PUT /joint/{id} 请求体"""
    # 全部设为 Optional，前端传了哪个字段就更新哪个字段
    joint_code: Optional[str] = Field(None, max_length=50, description="接头编号")
    joint_type: Optional[str] = Field(None, max_length=50, description="接头形式")
    groove_type: Optional[str] = Field(None, max_length=50, description="焊接坡口")
    t1_thickness: Optional[Decimal] = Field(None, ge=0, description="t1工件尺寸(mm)")
    t2_thickness: Optional[Decimal] = Field(None, ge=0, description="t2工件尺寸(mm)")
    weld_layers: Optional[int] = Field(None, gt=0, description="焊层数量")
    welding_gap: Optional[Decimal] = Field(None, ge=0, description="焊接间隙(mm)")
    description: Optional[str] = Field(None, description="接头补充说明")

class WeldingJointQuery(BaseModel):
    """【查询】GET 接口参数 (Query Params)"""
    joint_code: Optional[str] = Field(None, description="按接头编号模糊搜索")
    joint_type: Optional[str] = Field(None, description="按接头形式精确筛选")
    
    current: int = Field(1, ge=1, description="页码")
    pageSize: int = Field(10, gt=0, description="每页条数")