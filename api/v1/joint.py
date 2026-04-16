from models.joint import WeldingJoint
from fastapi import APIRouter, Path, Depends
from typing import Any
from schemas.response import resp
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from schemas.request import sys_joint_schema
from common.session import get_db

router = APIRouter()


@router.post("/joint/add", summary="添加焊接接头", name="新增一条接头信息")
async def add_welding_joint(req: sys_joint_schema.WeldingJointCreate) -> Any:
    try:
        joint_data = req.dict() 
        
        success, new_id, msg = await WeldingJoint.add_joint(joint_data)
        
        if success:
            return resp.ok(data={"id": new_id}, msg=msg)
        else:
            # 处理 unique=True 导致的重名冲突
            return resp.fail(resp.DataStoreFail.set_msg(msg))
            
    except Exception as e:
        # 系统级异常兜底
        print(f"新增接头发生系统异常: {str(e)}")
        return resp.fail(resp.DataStoreFail.set_msg(f"系统内部错误: {str(e)}"))
    
# ==========================================
# 1. 删 (DELETE)
# ==========================================
@router.delete("/joint/{joint_id}", summary="删除接头", name="根据ID删除焊接接头")
async def delete_welding_joint(
    joint_id: int = Path(..., description="接头数据库主键ID")
) -> Any:
    try:
        success, msg = await WeldingJoint.delete_joint(joint_id)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# ==========================================
# 2. 改 (PUT)
# ==========================================
@router.put("/joint/{joint_id}", summary="更新接头", name="更新指定的接头信息")
async def update_welding_joint(
    joint_id: int = Path(..., description="接头数据库主键ID"),
    req: sys_joint_schema.WeldingJointUpdate = None
) -> Any:
    try:
        # Pydantic V1 语法: 仅获取用户实际填写的字段，防止将未传的字段覆盖为 None
        update_data = req.dict(exclude_unset=True)
        if not update_data:
            return resp.fail(resp.DataStoreFail.set_msg("没有提供任何需要更新的数据"))

        success, msg = await WeldingJoint.update_joint(joint_id, update_data)
        if success:
            return resp.ok(msg=msg)
        return resp.fail(resp.DataStoreFail.set_msg(msg))
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"系统异常: {str(e)}"))

# ==========================================
# 3. 查 - 全部列表 (GET)
# ==========================================
@router.get("/joint/list/all", summary="获取所有接头", name="查询接头全量列表(不分页)")
async def get_all_welding_joints() -> Any:
    try:
        results = await WeldingJoint.get_all_joints()
        # 将 Peewee 模型实例转换为字典列表
        data = [joint.__data__ for joint in results]
        return resp.ok(data=data)
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"查询异常: {str(e)}"))

# ==========================================
# 4. 查 - 条件筛选与分页 (GET)
# ==========================================
@router.get("/joint/list/page", summary="分页筛选接头", name="按条件搜索并分页")
async def search_welding_joints(
    query: sys_joint_schema.WeldingJointQuery = Depends()
) -> Any:
    try:
        results, total = await WeldingJoint.filter_joints(
            code=query.joint_code,
            j_type=query.joint_type,
            page=query.current,
            page_size=query.pageSize
        )
        
        # 组装标准分页返回格式
        data = {
            "list": [joint.__data__ for joint in results],
            "total": total,
            "current": query.current,
            "pageSize": query.pageSize
        }
        return resp.ok(data=data)
    except Exception as e:
        return resp.fail(resp.DataStoreFail.set_msg(f"分页查询异常: {str(e)}"))