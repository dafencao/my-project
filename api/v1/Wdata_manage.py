from models.Wdata_manage import WProcessRecord
from fastapi import APIRouter, Path, Depends
from typing import Any
from schemas.response import resp
from schemas.request import Wdata_manage_schema

router = APIRouter()

from fastapi import APIRouter, Depends, Path
from typing import Any


router = APIRouter()

# --- 1. 新增记录 ---
@router.post("/process/add", summary="新增工艺与实验记录", name="关联数据集与工艺参数")
async def add_process_record(req: Wdata_manage_schema.WProcessRecordCreate) -> Any:
    try:
        data = req.dict()
        success, new_id, msg = await WProcessRecord.add_record(data)
        if success:
            return resp.ok(data={"id": new_id}, msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 2. 删除记录 ---
@router.delete("/process/{record_id}", summary="删除实验记录", name="根据ID删除")
async def delete_process_record(record_id: int = Path(...)) -> Any:
    try:
        success, msg = await WProcessRecord.delete_record(record_id)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 3. 更新记录 ---
@router.put("/process/{record_id}", summary="更新实验记录", name="修改参数或锁定状态")
async def update_process_record(
    record_id: int = Path(...),
    req: Wdata_manage_schema.WProcessRecordUpdate = None
) -> Any:
    try:
        # Pydantic V1: 仅提取前端传了值的字段
        update_data = req.dict(exclude_unset=True)
        if not update_data:
            return resp.fail(resp.DataStoreFail.set_msg("没有提供任何需要更新的数据"))

        success, msg = await WProcessRecord.update_record(record_id, update_data)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# --- 4. 后台管理查询 ---
@router.get("/process/search", summary="后台查询记录", name="分页及条件筛选")
async def search_process_records(query: Wdata_manage_schema.WProcessRecordQuery = Depends()) -> Any:
    try:
        results, total = await WProcessRecord.filter_records(
            name=query.record_name,
            dataset=query.dataset_type,
            batch=query.batch_tag,
            m_id=query.material_id,
            page=query.current,
            page_size=query.pageSize
        )
        
        data = {
            "list": [r.__data__ for r in results],
            "total": total,
            "current": query.current,
            "pageSize": query.pageSize
        }
        return resp.ok(data=data)
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"查询异常: {str(e)}"))

# --- 5. 专供深度学习模型的拉取接口 ---
@router.get("/process/ml_dataset", summary="拉取模型数据集", name="深度学习 DataLoader 专用")
async def get_ml_dataset(query: Wdata_manage_schema.MLDatasetQuery = Depends()) -> Any:
    """
    不分页，直接返回满足条件的所有数据清单，供 Python 训练脚本调用。
    """
    try:
        results = await WProcessRecord.get_dataset_for_ml(
            dataset_type=query.dataset_type,
            batch_tag=query.batch_tag
        )
        
        # 精简返回结构，只给模型需要的核心字段
        dataset = []
        for r in results:
            dataset.append({
                "id": r.id,
                "file_path": r.file_path,  # ML 脚本拿到后自行拼接 DATA_ROOT
                "speed": float(r.welding_speed) if r.welding_speed else None,
                "heat_input": float(r.heat_input) if r.heat_input else None,
                "parameters": r.parameters # JSON 直接透传为 Python 字典
            })
            
        return resp.ok(data={"count": len(dataset), "dataset": dataset}, msg="数据集拉取成功")
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"数据集拉取异常: {str(e)}"))