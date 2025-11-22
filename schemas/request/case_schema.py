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
    case_picture: Optional[str] = Field("", description="焊接图片地址")



class CaseQualityUpdate(BaseModel):
    """更新案例质量请求模型"""
    case_id: Optional[str] = Field(None, description="案例唯一标识(格式:CAS-序号)")
    related_process_id: Optional[str] = Field(None, description="关联工艺ID(关联process_design表)")
    product_name: Optional[str] = Field(None, description="产品名称(如油箱壳体、安装座、机匣)")
    product_size: Optional[str] = Field(None, description="产品尺寸(格式:长*宽*高/厚度,如300*100*2.1mm)")
    weld_depth: Optional[Decimal] = Field(None, description="焊缝熔深(mm,实测值)")
    weld_width: Optional[Decimal] = Field(None, description="焊缝熔宽(mm,实测值)")
    tensile_strength: Optional[int] = Field(None, description="焊接接头拉伸强度(MPa)")
    deformation_amount: Optional[Decimal] = Field(None, description="变形量(mm,如径向变形、整体变形)")
    defect_type: Optional[str] = Field(None, description="缺陷类型(无/气孔/裂纹/未熔合,多缺陷用'、'分隔)")
    defect_position: Optional[str] = Field(None, description="缺陷位置(如焊缝中心,无缺陷填'无')")
    defect_cause: Optional[str] = Field(None, description="缺陷成因(如焊接速度过快,无缺陷填'无')")
    detection_method: Optional[str] = Field(None, description="检测方法(如超声检测、X光检测、目视检测)")
    detection_result: Optional[str] = Field(None, description="检测结果")
    inspection_standard: Optional[str] = Field(None, description="检验标准(如I级焊缝、企业标准)")
    case_picture: Optional[str] = Field("", description="焊接图片地址")


class CaseQualityFilter(BaseModel):
    """焊接案例筛选条件"""
    case_id: Optional[str] = Field(None, description="案例ID")
    related_process_id: Optional[str] = Field(None, description="关联工艺ID")
    product_name: Optional[str] = Field(None, description="产品名称")
    product_size: Optional[str] = Field(None, description="产品尺寸")
    
    # 焊缝质量参数筛选
    weld_depth_min: Optional[Decimal] = Field(None, description="最小焊缝熔深(mm)")
    weld_depth_max: Optional[Decimal] = Field(None, description="最大焊缝熔深(mm)")
    weld_width_min: Optional[Decimal] = Field(None, description="最小焊缝熔宽(mm)")
    weld_width_max: Optional[Decimal] = Field(None, description="最大焊缝熔宽(mm)")
    tensile_strength_min: Optional[int] = Field(None, description="最小拉伸强度(MPa)")
    tensile_strength_max: Optional[int] = Field(None, description="最大拉伸强度(MPa)")
    deformation_amount_min: Optional[Decimal] = Field(None, description="最小变形量(mm)")
    deformation_amount_max: Optional[Decimal] = Field(None, description="最大变形量(mm)")
    
    # 缺陷相关筛选
    defect_type: Optional[str] = Field(None, description="缺陷类型")
    defect_position: Optional[str] = Field(None, description="缺陷位置")
    defect_cause: Optional[str] = Field(None, description="缺陷成因")
    
    # 检测相关筛选
    detection_method: Optional[str] = Field(None, description="检测方法")
    detection_result: Optional[str] = Field(None, description="检测结果")
    inspection_standard: Optional[str] = Field(None, description="检验标准")
    
    # 关联工艺参数筛选（用于跨表查询）
    laser_power_min: Optional[int] = Field(None, description="最小激光功率(W)")
    laser_power_max: Optional[int] = Field(None, description="最大激光功率(W)")
    welding_speed_min: Optional[int] = Field(None, description="最小焊接速度(mm/min)")
    welding_speed_max: Optional[int] = Field(None, description="最大焊接速度(mm/min)")
    defocus_amount_min: Optional[Decimal] = Field(None, description="最小离焦量(mm)")
    defocus_amount_max: Optional[Decimal] = Field(None, description="最大离焦量(mm)")
    
    # 关联材料筛选
    base_material: Optional[str] = Field(None, description="母材类型")
    material_grade: Optional[str] = Field(None, description="材料牌号")
    
    # 关联设备筛选
    laser_equipment_model: Optional[str] = Field(None, description="激光设备型号")
    laser_power_range: Optional[str] = Field(None, description="激光功率范围")

    class Config:
        from_attributes = True