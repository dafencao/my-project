from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from decimal import Decimal


class EquipmentParamBase(BaseModel):
    """设备参数基础模型"""
    equipment_id: str = Field(..., min_length=1, max_length=20, description="设备唯一标识（格式：EQU-序号）")
    laser_equipment_model: str = Field(..., min_length=1, max_length=100, description="激光设备型号")
    laser_power_range: str = Field(..., min_length=1, max_length=20, description="激光功率范围（格式：最小值-最大值，单位W）")
    output_mode: str = Field(..., description="激光输出方式")
    laser_wavelength: Optional[int] = Field(default=0, ge=0, description="激光波长（nm）")
    spot_diameter: Optional[Union[Decimal, float]] = Field(default=0.00, ge=0, description="光斑直径（mm，聚焦后尺寸）")
    auxiliary_equipment_type: Optional[str] = Field(default="", max_length=50, description="辅助设备类型（如焊接工装、夹具）")
    auxiliary_equipment_model: Optional[str] = Field(default="", max_length=50, description="辅助设备型号")
    sensor_type: Optional[str] = Field(default="", max_length=50, description="传感器类型（如温度传感器、应力传感器）")
    sensor_precision: Optional[str] = Field(default="", max_length=30, description="传感器精度（如±0.1℃）")

class EquipmentParamUpdate(BaseModel):
    """更新设备参数请求模型"""
    equipment_id: Optional[str] = Field(None, min_length=1, max_length=20)
    laser_equipment_model: Optional[str] = Field(None, min_length=1, max_length=100)
    laser_power_range: Optional[str] = Field(None, min_length=1, max_length=20)
    output_mode: Optional[str] = Field(None)
    laser_wavelength: Optional[int] = Field(None, ge=0)
    spot_diameter: Optional[Union[Decimal, float]] = Field(None, ge=0, le=999.99)
    auxiliary_equipment_type: Optional[str] = Field(None, max_length=50)
    auxiliary_equipment_model: Optional[str] = Field(None, max_length=50)
    sensor_type: Optional[str] = Field(None, max_length=50)
    sensor_precision: Optional[str] = Field(None, max_length=30)

class EquipmentFilter(BaseModel):
    """设备筛选条件"""
    laser_equipment_model: Optional[str] = Field(None, description="激光设备型号")
    output_mode: Optional[str] = Field(None, description="激光输出方式")
    laser_power_min: Optional[int] = Field(None, description="最小激光功率(W)")
    laser_power_max: Optional[int] = Field(None, description="最大激光功率(W)")
    laser_wavelength_min: Optional[int] = Field(None, description="最小激光波长(nm)")
    laser_wavelength_max: Optional[int] = Field(None, description="最大激光波长(nm)")
    spot_diameter_min: Optional[Decimal] = Field(None, description="最小光斑直径(mm)")
    spot_diameter_max: Optional[Decimal] = Field(None, description="最大光斑直径(mm)")
    auxiliary_equipment_type: Optional[str] = Field(None, description="辅助设备类型")
    sensor_type: Optional[str] = Field(None, description="传感器类型")

    class Config:
        from_attributes = True
