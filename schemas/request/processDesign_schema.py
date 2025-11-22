from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum


class GrooveType(str, Enum):
    NO_GROOVE = "无坡口"
    V_GROOVE = "V型坡口"
    U_GROOVE = "U型坡口"
    X_GROOVE = "X型坡口"

class ProcessDesignBase(BaseModel):
    process_id: str = Field(..., description="工艺唯一标识(格式:PRO-序号)")
    related_material_id: str = Field(..., description="关联材料ID(关联material_info表)")
    related_equipment_id: str = Field(..., description="关联设备ID(关联equipment_param表)")
    laser_power: int = Field(..., ge=0, description="激光功率(W,实际设定值)")
    welding_speed: int = Field(..., ge=0, description="焊接速度(mm/min)")
    defocus_amount: Decimal = Field(..., description="离焦量(mm,正值正离焦,负值负离焦)")
    incident_angle: Decimal = Field(..., description="入射角度(°,激光束与工件表面夹角)")
    welding_sequence: str = Field("", description="焊接顺序(如纵缝、先内后外)")
    groove_type: GrooveType = Field(..., description="坡口形式")
    groove_angle: int = Field(0, ge=0, le=180, description="坡口角度(°,无坡口填0)")
    joint_type: str = Field(..., description="接头形式(如锁底对接、搭接、角接)")
    joint_thickness: Decimal = Field(..., gt=0, description="接头厚度(mm)")
    scanning_mode: str = Field("无", description="扫描方式(如8字型,无则填'无')")
    scanning_frequency: int = Field(0, ge=0, description="扫描频率(Hz,无扫描填0)")
    scanning_amplitude: Decimal = Field(0.00, ge=0, description="扫描幅值(mm,无扫描填0)")
    heat_treatment_method: str = Field("无", description="热处理方法(如真空退火,无则填'无')")
    heat_treatment_temp: int = Field(0, ge=0, description="热处理温度(℃,无热处理填0)")
    heat_treatment_time: Decimal = Field(0.0, ge=0, description="热处理时间(h,无热处理填0)")
    heat_input: Decimal = Field(0.00, ge=0, description="热输入量(J·mm⁻¹)")


class ProcessDesignUpdate(BaseModel):
    process_id: Optional[str] = Field(None, description="工艺唯一标识(格式:PRO-序号)")
    related_material_id: Optional[str] = Field(None, description="关联材料ID(关联material_info表)")
    related_equipment_id: Optional[str] = Field(None, description="关联设备ID(关联equipment_param表)")
    laser_power: Optional[int] = Field(None, ge=0)
    welding_speed: Optional[int] = Field(None, ge=0)
    defocus_amount: Optional[Decimal] = Field(None)
    incident_angle: Optional[Decimal] = Field(None)
    welding_sequence: Optional[str] = Field(None)
    groove_type: Optional[GrooveType] = Field(None)
    groove_angle: Optional[int] = Field(None, ge=0, le=180)
    joint_type: Optional[str] = Field(None)
    joint_thickness: Optional[Decimal] = Field(None, gt=0)
    scanning_mode: Optional[str] = Field(None)
    scanning_frequency: Optional[int] = Field(None, ge=0)
    scanning_amplitude: Optional[Decimal] = Field(None, ge=0)
    heat_treatment_method: Optional[str] = Field(None)
    heat_treatment_temp: Optional[int] = Field(None, ge=0)
    heat_treatment_time: Optional[Decimal] = Field(None, ge=0)
    heat_input: Optional[Decimal] = Field(None, ge=0)


class ProcessDesignFilter(BaseModel):
    """焊接工艺筛选条件"""
    process_id: Optional[str] = Field(None, description="工艺ID")
    related_material_id: Optional[str] = Field(None, description="关联材料ID")
    related_equipment_id: Optional[str] = Field(None, description="关联设备ID")
    
    # 激光参数筛选
    laser_power_min: Optional[int] = Field(None, description="最小激光功率(W)")
    laser_power_max: Optional[int] = Field(None, description="最大激光功率(W)")
    welding_speed_min: Optional[int] = Field(None, description="最小焊接速度(mm/min)")
    welding_speed_max: Optional[int] = Field(None, description="最大焊接速度(mm/min)")
    defocus_amount_min: Optional[Decimal] = Field(None, description="最小离焦量(mm)")
    defocus_amount_max: Optional[Decimal] = Field(None, description="最大离焦量(mm)")
    incident_angle_min: Optional[Decimal] = Field(None, description="最小入射角度(°)")
    incident_angle_max: Optional[Decimal] = Field(None, description="最大入射角度(°)")
    
    # 坡口和接头筛选
    groove_type: Optional[str] = Field(None, description="坡口形式")
    groove_angle_min: Optional[int] = Field(None, description="最小坡口角度(°)")
    groove_angle_max: Optional[int] = Field(None, description="最大坡口角度(°)")
    joint_type: Optional[str] = Field(None, description="接头形式")
    joint_thickness_min: Optional[Decimal] = Field(None, description="最小接头厚度(mm)")
    joint_thickness_max: Optional[Decimal] = Field(None, description="最大接头厚度(mm)")
    
    # 扫描参数筛选
    scanning_mode: Optional[str] = Field(None, description="扫描方式")
    scanning_frequency_min: Optional[int] = Field(None, description="最小扫描频率(Hz)")
    scanning_frequency_max: Optional[int] = Field(None, description="最大扫描频率(Hz)")
    scanning_amplitude_min: Optional[Decimal] = Field(None, description="最小扫描幅值(mm)")
    scanning_amplitude_max: Optional[Decimal] = Field(None, description="最大扫描幅值(mm)")
    
    # 热处理筛选
    heat_treatment_method: Optional[str] = Field(None, description="热处理方法")
    heat_treatment_temp_min: Optional[int] = Field(None, description="最小热处理温度(℃)")
    heat_treatment_temp_max: Optional[int] = Field(None, description="最大热处理温度(℃)")
    heat_treatment_time_min: Optional[Decimal] = Field(None, description="最小热处理时间(h)")
    heat_treatment_time_max: Optional[Decimal] = Field(None, description="最大热处理时间(h)")
    
    # 热输入筛选
    heat_input_min: Optional[Decimal] = Field(None, description="最小热输入量(J·mm⁻¹)")
    heat_input_max: Optional[Decimal] = Field(None, description="最大热输入量(J·mm⁻¹)")

    class Config:
        from_attributes = True
