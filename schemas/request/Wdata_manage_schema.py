from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from decimal import Decimal

# ==========================================
# 1. 基础字段
# ==========================================
class WProcessRecordBase(BaseModel):
    record_name: str = Field(..., max_length=100, description="记录名称")
    dataset_type: str = Field(default="unassigned", description="数据集标识: train, val, test, unassigned")
    batch_tag: Optional[str] = Field(None, max_length=50, description="训练批次/版本标签")
    file_path: str = Field(..., max_length=255, description="Parquet文件的相对路径")
    
    material_id: int = Field(..., description="关联的母材ID")
    joint_id: int = Field(..., description="关联的接头ID")
    method_id: int = Field(..., description="关联的焊接方法ID")
    
    welding_speed: Optional[Decimal] = Field(None, ge=0, description="焊接速度 (mm/min)")
    heat_input: Optional[Decimal] = Field(None, ge=0, description="热输入特征 (kJ/mm)")
    
    # 核心：动态工艺参数字典
    parameters: Dict[str, Any] = Field(default={}, description="特定工艺的参数集合(JSON)")
    
    is_locked: bool = Field(default=False, description="数据锁定标识")
    description: Optional[str] = Field(None, description="实验备注")

# ==========================================
# 2. 新增接口请求体
# ==========================================
class WProcessRecordCreate(WProcessRecordBase):
    """【新增】POST /process/add"""
    pass # 继承全部必填/选填属性

# ==========================================
# 3. 更新接口请求体
# ==========================================
class WProcessRecordUpdate(BaseModel):
    """【更新】PUT /process/{id}"""
    record_name: Optional[str] = Field(None, max_length=100)
    dataset_type: Optional[str] = Field(None)
    batch_tag: Optional[str] = Field(None, max_length=50)
    file_path: Optional[str] = Field(None, max_length=255)
    material_id: Optional[int] = Field(None)
    joint_id: Optional[int] = Field(None)
    method_id: Optional[int] = Field(None)
    welding_speed: Optional[Decimal] = Field(None, ge=0)
    heat_input: Optional[Decimal] = Field(None, ge=0)
    parameters: Optional[Dict[str, Any]] = Field(None)
    is_locked: Optional[bool] = Field(None)
    description: Optional[str] = Field(None)

# ==========================================
# 4. 查询接口参数
# ==========================================
class WProcessRecordQuery(BaseModel):
    """【后台管理查询】GET /process/search"""
    record_name: Optional[str] = Field(None, description="按名称模糊搜索")
    dataset_type: Optional[str] = Field(None, description="按数据集类型筛选")
    batch_tag: Optional[str] = Field(None, description="按批次筛选")
    material_id: Optional[int] = Field(None, description="按母材ID筛选")
    current: int = Field(1, ge=1, description="页码")
    pageSize: int = Field(10, gt=0, description="每页条数")

class MLDatasetQuery(BaseModel):
    """【模型专门拉取数据】GET /process/ml_dataset"""
    dataset_type: str = Field(..., description="必须指定拉取 train / val / test")
    batch_tag: Optional[str] = Field(None, description="按批次精确拉取")