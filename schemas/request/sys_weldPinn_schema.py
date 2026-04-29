from pydantic import BaseModel, Field
from typing import List, Optional

class SinglePointPredictRequest(BaseModel):
    """单点预测请求体"""
    x: float = Field(..., description="X 坐标")
    y: float = Field(..., description="Y 坐标")
    z: float = Field(..., description="Z 坐标")
    time: float = Field(..., description="时间点 (s)")
    power: float = Field(3500.0, description="功率 (W)")
    speed: float = Field(45.0, description="速度 (mm/s)")
    radius: float = Field(0.35, description="热源半径 (mm)")
    depth: float = Field(3.1, description="热源深度 (mm)")
    model_id: int = Field(..., description="关联的预训练模型(ProcessRecord) ID")
    material_id: int = Field(..., description="关联的母材 ID")

class BatchPredictRequest(BaseModel):
    """批量云图预测请求体"""
    material_id: int = Field(..., description="使用的母材 ID")
    joint_id: int = Field(..., description="接头类型 ID")
    method_id: int = Field(..., description="焊接工艺 ID")
    
    # 空间网格划分 (精度)
    nx: int = Field(50, description="X轴网格数")
    ny: int = Field(10, description="Y轴网格数")
    nz: int = Field(100, description="Z轴网格数")
    
    # 预测时刻序列
    time_points: List[float] = Field([0.5, 1.0], description="需要预测的时刻列表")
    
    # 动态工艺参数
    power: float = Field(..., description="功率 (W)")
    speed: float = Field(..., description="焊接速度 (mm/s)")
    radius: float = Field(0.35, description="热源半径 (mm)")
    depth: float = Field(3.1, description="热源深度 (mm)")

class TrainStartRequest(BaseModel):
    joint_id: int = Field(..., description="要训练的接头 ID")
    method_id: int = Field(..., description="要训练的工艺 ID")
    version: str = Field("V1.0", description="模型版本")
    description: str = Field("系统自动发起的训练任务", description="模型备注")
    epochs: int = Field(15000, description="训练轮数")