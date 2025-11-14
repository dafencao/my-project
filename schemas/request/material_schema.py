from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class MatericalBase(BaseModel):
    material_id: Optional[str] = Field("", description="化学成分（如Ti-6Al-4V）")
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