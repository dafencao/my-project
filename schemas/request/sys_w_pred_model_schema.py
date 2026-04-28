# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any,List

class TrainedModelCreate(BaseModel):
    """【新增】注册新通用模型"""
    model_name: str = Field(..., max_length=100)
    version: str = Field(..., max_length=50)
    model_path: str = Field(..., max_length=255)
    
    joint_id: int = Field(..., description="关联的接头ID")
    method_id: int = Field(..., description="关联的焊接方法ID")
    trained_material_ids: Optional[List[int]] = Field(default=[], description="训练时使用的母材ID列表")
    
    max_def_rel_error: Optional[float] = Field(None, description="最大变形量相对误差 (%)")
    description: Optional[str] = None
    trained_on_batch: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    is_deployed: bool = Field(default=False)

class TrainedModelUpdate(BaseModel):
    """【更新】修改模型信息或上线状态"""
    model_name: Optional[str] = Field(None, max_length=100)
    version: Optional[str] = Field(None, max_length=50)
    trained_material_ids: Optional[List[int]] = None
    max_def_rel_error: Optional[float] = None
    description: Optional[str] = None
    is_deployed: Optional[bool] = None

class TrainedModelQuery(BaseModel):
    """【查询】后台管理列表查询"""
    joint_id: Optional[int] = None
    method_id: Optional[int] = None
    is_deployed: Optional[bool] = None
    current_page: int = Field(1, ge=1)
    page_size: int = Field(10, gt=0)