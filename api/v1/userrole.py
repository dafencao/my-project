'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-05-10 14:12:52
'''
import pytz

from utils.tools_func import tz

'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-04-19 14:48:02
'''

from models.userrole import Permission, RoleMenuRelp, RolePermRelp, Userrole
from common import deps, logger
from common.session import db, async_db
from core import security
from fastapi import APIRouter, Depends, HTTPException, Form,HTTPException, status
from datetime import datetime, timedelta
from typing import Any,List
from schemas.response import resp
from schemas.request import sys_userrole_schema
from models.user import UserRoleRelp, Userinfo
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
import asyncio

router = APIRouter()


@router.post("/sys/role/add", summary="添加角色", name="新增一条用户记录")
async def role_add(req: sys_userrole_schema.RoleCreate):
    permission_ids: List[int] = []
    permission_ids = getattr(req, 'permissionIds') 
    role = req.dict(exclude={'permissionIds'})
    role['create_at'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    role['update_at'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    
    try:
        async with db.atomic_async():
            roleId = await Userrole.add_role(role)
            for m_id in permission_ids:
                await RoleMenuRelp.add({'role_id': roleId, 'menu_id': m_id,'create_at':role['create_at']})
        return resp.ok(data=roleId)
        
    
    except IntegrityError as e:
        # 更精确地判断错误类型
        error_msg = str(e).lower()
        if 'unique' in error_msg or 'duplicate' in error_msg:
            return resp.fail(resp.DataStoreFail.set_msg('角色编码已存在！'))
        else:
            return resp.fail(resp.DataStoreFail.set_msg('数据完整性错误'))
    
    except Exception as e:
        print(f"添加角色失败: {e}")
        return resp.fail(resp.DataStoreFail, detail=str(e))   



@router.post("/sys/role/delete/{role_id}", summary="删除角色", name="删除角色")
async def del_user(
        id: int
) -> Any:
    print(id)
    try:
        async with db.atomic_async():
            await Userrole.del_by_userroleid(id)
            await UserRoleRelp.delete_by_roleId(id)
            await RoleMenuRelp.delete_by_roleId(id)
            await RolePermRelp.delete_by_roleId(id)
            return resp.ok(data=id)
    except Exception as e:
        return resp.fail(resp.DataDestroyFail, detail=str(e))





# /sys/role/queryall
@router.get("/role/all", summary="查询所有角色记录", name="查询所有角色记录")
async def query_all() -> Any:
    try:
        data = await Userrole.select_all()
        #  print("这是全部角色",data)
        return resp.ok(data=data)
    except Exception as e:

        return resp.fail(resp.DataNotFound, detail=str(e))


@router.post("/role/show", summary="任意字段筛选角色记录", name="任意字段筛选角色记录")
async def show_userrole(req: sys_userrole_schema.userroleQuery) -> Any:
    try:
        result =await  Userrole.fuzzy_query(req)
        total = len(result)
        current = int(req.current)
        pageSize = int(req.pageSize)
        result = result[
                 (current * pageSize - pageSize):
                 current * pageSize
                 ]
        return resp.ok(data=result, total=total)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))


@router.get("/sys/role/queryById", summary="根据角色id查看角色详细信息", name="查询角色详情")
async def query_user_id(id: int):
    result = await Userrole.select_by_id(id)
    print(f"查询结果: {result}")
    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="角色不存在")


@router.get("/sys/permission/queryRoleMenu/{role_id}", summary="根据角色id查看角色权限和菜单", name="查询角色详情")
async def get_role_all_permissions(role_id: int):
    # try:
    #     result = await RoleMenuRelp.selectMenu_by_role_id(role_id)
    #     return result
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"查询角色菜单失败: {str(e)}"
    #     )
    """
    获取角色的所有权限信息（菜单 + 权限）
    """
    try:
        if role_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色ID必须大于0"
            )
        
        # 并行执行两个查询
        menu_result, permission_result = await asyncio.gather(
            RoleMenuRelp.select_menus_by_role_id(role_id),
            RoleMenuRelp.select_permissions_by_role_id(role_id),
            return_exceptions=True  # 防止一个查询失败影响另一个
        )
        
        # 处理异常
        if isinstance(menu_result, Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询菜单权限失败: {str(menu_result)}"
            )
        
        if isinstance(permission_result, Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询功能权限失败: {str(permission_result)}"
            )
        
        return {
            "role_id": role_id,
            "menu_permissions": menu_result.get('menu_ids', []),
            "function_permissions": permission_result.get('permission_ids', []),
            "all_permissions": {
                "menus": menu_result.get('menu_ids', []),
                "permissions": permission_result.get('permission_ids', [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色权限失败: {str(e)}"
        )


@router.post("/sys/role/edit", summary="角色更新", name="角色更新")
async def role_update(req: sys_userrole_schema.RoleUpdate):
    req = dict(req)
    # return resp.fail(resp.DataUpdateFail )

    req['updateAt'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    role = dict_to_model(Userrole, req)
    try:
        await Userrole.update_by_model(role)
        # role.save()
        return resp.ok()
    except IntegrityError as e:

        return resp.fail(resp.DataUpdateFail.set_msg('角色编码已存在！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))


@router.post("/sys/permission/saveRolePermission", summary="保存角色的权限。", name="保存角色的权限。")
async def saveRolePermission(req: sys_userrole_schema.RoleMenuPerm):
    try:
        async with db.atomic_async():
            for id in req.permissionIds:
                if id not in req.lastpermissionIds:
                    # RoleMenuRelp.create(
                    #     roleId=req.roleId,
                    #     menuId=id)
                    await RoleMenuRelp.add({'roleId': req.roleId, 'menuId': id})
            for id in req.lastpermissionIds:
                if id not in req.permissionIds:
                    # print('delete')
                    # print(id)
                    # print('req.roleId')
                    # print(req.roleId)
                    # result = list(RoleMenuRelp.select().where(RoleMenuRelp.roleId ==
                    #                                           req.roleId, RoleMenuRelp.menuId == id).dicts())
                    # print(result)
                    # result = RoleMenuRelp.delete().where(RoleMenuRelp.roleId ==
                    #                                      req.roleId, RoleMenuRelp.menuId == id).execute()
                    result = await RoleMenuRelp.delete_by_roleId_and_menuId(req.roleId, id)
                    print(result)
            return resp.ok()
    except Exception as e:
        return resp.fail(resp.DataUpdateFail, detail=str(e))

