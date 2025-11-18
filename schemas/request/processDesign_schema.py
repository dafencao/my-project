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

