from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum


class CaseQualityBase(BaseModel):
    case_id: str = Field(..., description="案例唯一标识(格式:CAS-序号)")
    related_process_id: str = Field(..., description="关联工艺ID(关联process_design表)")
    product_name: str = Field(..., description="产品名称(如油箱壳体、安装座、机匣)")
    product_size: str = Field(..., description="产品尺寸(格式:长*宽*高/厚度,如300*100*2.1mm)")
    weld_depth: Optional[Decimal] = Field(0.00, description="焊缝熔深(mm,实测值)")
    weld_width: Optional[Decimal] = Field(0.00, description="焊缝熔宽(mm,实测值)")
    tensile_strength: Optional[int] = Field(0, description="焊接接头拉伸强度(MPa)")
    deformation_amount: Decimal = Field(..., description="变形量(mm,如径向变形、整体变形)")
    defect_type: str = Field(..., description="缺陷类型(无/气孔/裂纹/未熔合,多缺陷用'、'分隔)")
    defect_position: Optional[str] = Field("无", description="缺陷位置(如焊缝中心,无缺陷填'无')")
    defect_cause: Optional[str] = Field("无", description="缺陷成因(如焊接速度过快,无缺陷填'无')")
    detection_method: Optional[str] = Field("", description="检测方法(如超声检测、X光检测、目视检测)")
    detection_result: str = Field(..., description="检测结果")
    inspection_standard: Optional[str] = Field("", description="检验标准(如I级焊缝、企业标准)")