from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class MatericalBase(BaseModel):
    material_id: Optional[str] = Field("",description='材料ID')
    base_material: str = Field(..., description="母材材质（如TC4钛合金、6061铝合金）")
    material_grade: Optional[str] = Field("", description="母材牌号（行业标准牌号）")
    chemical_composition: Optional[str] = Field("", description="化学成分（如Ti-6Al-4V）")
    tensile_strength: Optional[int] = Field(0, description="抗拉强度（MPa，室温测试值）")
    hardness: Optional[Decimal] = Field(Decimal('0.0'), description="硬度（HRC）")
    melting_point: Optional[int] = Field(0, description="熔点（℃）")
    thermal_conductivity: Optional[Decimal] = Field(Decimal('0.00'), description="热导率（W/(m·K)，室温测试值）")
    filler_wire_spec: Optional[str] = Field("无", description="填充焊丝规格（无则填'无'）")
    shielding_gas_type: str = Field(..., description="保护气类型（如氩气、氦气）")
    shielding_gas_purity: Optional[Decimal] = Field(Decimal('0.00'), description="保护气纯度（%）")


class MaterialUpdate(BaseModel):
    material_id: Optional[str] = Field("",description='材料ID')
    base_material: str = None
    material_grade: Optional[str] = None
    chemical_composition: Optional[str] = None
    tensile_strength: Optional[int] = None
    hardness: Optional[Decimal] = None
    melting_point: Optional[int] = None
    thermal_conductivity: Optional[Decimal] = None
    filler_wire_spec: Optional[str] = None
    shielding_gas_type: Optional[str] = None 
    shielding_gas_purity: Optional[Decimal] = None


class MaterialFilter(BaseModel):
    base_material: Optional[str] = Field(None, description="母材材质")
    material_grade: Optional[str] = Field(None, description="母材牌号")
    chemical_composition: Optional[str] = Field(None, description="化学成分")
    tensile_strength_min: Optional[int] = Field(None, description="抗拉强度最小值")
    tensile_strength_max: Optional[int] = Field(None, description="抗拉强度最大值")
    hardness_min: Optional[Decimal] = Field(None, description="硬度最小值")
    hardness_max: Optional[Decimal] = Field(None, description="硬度最大值")
    melting_point_min: Optional[int] = Field(None, description="熔点最小值")
    melting_point_max: Optional[int] = Field(None, description="熔点最大值")
    thermal_conductivity_min: Optional[Decimal] = Field(None, description="热导率最小值")
    thermal_conductivity_max: Optional[Decimal] = Field(None, description="热导率最大值")
    filler_wire_spec: Optional[str] = Field(None, description="填充焊丝规格")
    shielding_gas_type: Optional[str] = Field(None, description="保护气类型")
    shielding_gas_purity_min: Optional[Decimal] = Field(None, description="保护气纯度最小值")
    shielding_gas_purity_max: Optional[Decimal] = Field(None, description="保护气纯度最大值")
    
    class Config:
        json_encoders = {
            Decimal: str
        }