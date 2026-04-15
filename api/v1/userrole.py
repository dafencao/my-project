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

from models.userrole import Permission, RoleMenuRelp, Userrole
from common.session import db, async_db
from fastapi import APIRouter, Depends, HTTPException, Form, status
from datetime import datetime
from typing import Any,List
from schemas.response import resp
from schemas.request import sys_userrole_schema
from models.user import UserRoleRelp
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from models.usermenu import Usermenu

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



@router.post("/sys/role/delete", summary="删除角色", name="删除角色")
async def del_user(
        id: dict
) -> Any:
    id=id['id']
    try:
        async with db.atomic_async():
            await Userrole.del_by_userroleid(id)
            await UserRoleRelp.delete_by_roleId(id)
            await RoleMenuRelp.delete_by_roleId(id)
            # await RolePermRelp.delete_by_roleId(id)
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
        
        
        menu_result = await RoleMenuRelp.selectMenu_by_role_id(role_id)       
        print(menu_result)
        
        # 处理异常
        if not menu_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到角色 {role_id} 的权限信息"
            )
        
        # if isinstance(permission_result, Exception):
        #     raise HTTPException(
        #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         detail=f"查询功能权限失败: {str(permission_result)}"
        #     )
        
        return {
            "role_id": role_id,
            "menu_ids": menu_result.get('menu_ids', [])
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

    req['update_at'] = datetime.strftime(
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

@router.post("/sys/permission/saveRoleMenu", summary="新增角色的菜单权限", name="新增角色的菜单权限")
async def add_Role_Menu(req: sys_userrole_schema.RoleMenuPerm):
    try:
        # 1. 获取系统中所有有效的菜单ID
        all_menu_ids_result = await Usermenu.select_all_menu_id()
        
        # 转换格式
        if all_menu_ids_result and isinstance(all_menu_ids_result[0], dict):
            valid_menu_ids = [item['menu_id'] for item in all_menu_ids_result]
        elif all_menu_ids_result and isinstance(all_menu_ids_result[0], tuple):
            valid_menu_ids = [item[0] for item in all_menu_ids_result]
        else:
            valid_menu_ids = all_menu_ids_result or []
        
        # 2. 查询角色已有的菜单权限
        role_permissions = await RoleMenuRelp.selectMenu_by_role_id(req.role_id)  
        current_menu_ids = role_permissions.get('menu_ids', [])
        
        async with db.atomic_async():
            added_count = 0
            duplicate_count = 0
            invalid_count = 0
            
            for menu_id in req.menu_id:
                # 检查菜单ID是否有效
                if menu_id not in valid_menu_ids:
                    invalid_count += 1
                    continue
                
                # 检查是否已存在
                if menu_id in current_menu_ids:
                    duplicate_count += 1
                    continue
                
                # 添加新的菜单权限
                await RoleMenuRelp.add({
                    'role_id': req.role_id,
                    'menu_id': menu_id
                })
                added_count += 1
            
            # 返回结果
            if added_count == 0:
                if duplicate_count > 0:
                    return resp.fail(
                        resp.DataStoreFail,
                        detail=f"所有菜单权限都已存在"
                    )
                if invalid_count > 0:
                    return resp.fail(
                        resp.DataNotFound,
                        detail=f"所有菜单ID无效"
                    )
                return resp.fail(resp.DataUpdateFail, detail="未添加任何权限")
            
            message = f"成功新增 {added_count} 个菜单权限"
            if duplicate_count > 0:
                message += f"，跳过 {duplicate_count} 个已存在的权限"
            if invalid_count > 0:
                message += f"，忽略 {invalid_count} 个无效菜单ID"
            
            return resp.ok(data={"message": message})
            
    except Exception as e:
        return resp.fail(resp.DataUpdateFail, detail=str(e))

@router.delete("/sys/permission/delete", summary="删除角色的菜单权限", name="删除角色的菜单权限")
async def del_rolemenu(
    req: sys_userrole_schema.RoleMenuDelete
):
    try:
        deleted_count = 0
        failed_menu_ids = []
        async with db.atomic_async():
            for menu_id in req.menu_id:
                try:
                    result = await RoleMenuRelp.delete_by_roleId_and_menuId(
                        req.role_id, 
                        menu_id
                    )
                    if result:
                        deleted_count += 1
                except Exception as menu_error:
                    failed_menu_ids.append({
                        "menu_id": menu_id,
                        "error": str(menu_error)
                    })
        return resp.ok()
        
    except Exception as e:
        print(f"批量删除失败: {e}")
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    
@router.put("/sys/permission/updateRoleMenu", summary="修改角色的菜单权限", name="修改角色的菜单权限")
async def update_role_menu(
   req: sys_userrole_schema.RoleMenuUpdate
):  
 
    try: 
        #1. 查询角色的当前所有菜单权限
        role_permissions = await RoleMenuRelp.selectMenu_by_role_id(req.role_id)  
        current_menu_ids = role_permissions.get('menu_ids', [])
        menu_ids=await Usermenu.select_all_menu_id()
        # 验证新旧ID不能相同  
        async with db.atomic_async():   
        # 3. 检查新menu_id是否已存在
         if req.new_menu_id in current_menu_ids:
            return resp.fail(
                resp.DataUpdateFail, 
                detail=f"角色 {req.role_id} 已拥有菜单权限 {req.new_menu_id}"
            )
       
          
            # 2. 检查旧menu_id（req.menu_id）是否存在
        if req.new_menu_id not in  menu_ids:
              return resp.fail(
                 resp.DataNotFound, 
                 detail=f"没有菜单权限 {req.new_menu_id}"
              )
            
         
            # 添加新的权限
        await RoleMenuRelp.add({
                'role_id': req.role_id,
                'menu_id': req.new_menu_id
            })
            
            # 5. 查询更新后的权限
            
        return resp.ok(data={
                "message": f"成功将菜单权限修改为 {req.new_menu_id}",
                }
            )
            
    except Exception as e:
        return resp.fail(resp.DataUpdateFail, detail=str(e))

@router.post("/sys/permission/queryRoleMenu", summary="查询角色-菜单权限关系", name="查询角色-菜单权限关系")
async def query_role_menu(req: sys_userrole_schema.RoleMenuQuery):
    try:
        # 验证参数
        if req.role_id is None and req.menu_id is None:
            return resp.fail(resp.DataQueryFail, detail="请输入要查询的参数")
        
        # 情况1：只提供role_id
        if req.role_id is not None and req.menu_id is None:
            role_permissions = await RoleMenuRelp.selectMenu_by_role_id(req.role_id)
            
            return resp.ok(data={
                "role_id": req.role_id,
                "menu_ids": role_permissions.get('menu_ids', [])
            })
        
        # 情况2：只提供menu_id
        elif req.menu_id is not None and req.role_id is None:
            result = await async_db.execute(
                RoleMenuRelp.select(RoleMenuRelp.role_id)
                .where(RoleMenuRelp.menu_id == req.menu_id)
                .dicts()
            )
            
            role_ids = [row['role_id'] for row in result] if result else []
            
            return resp.ok(data={
                "menu_id": req.menu_id,
                "role_ids": role_ids
            })
        
        # 情况3：同时提供role_id和menu_id
        else:
            result = await async_db.execute(
                RoleMenuRelp.select()
                .where(
                    RoleMenuRelp.role_id == req.role_id,
                    RoleMenuRelp.menu_id == req.menu_id
                )
                .dicts()
            )
            
            # 直接返回是否存在记录
            exists = len(result) > 0
            
            return resp.ok(data={
                "role_id": req.role_id,
                "menu_id": req.menu_id,
                "exists": exists
            })
            
    except Exception as e:
        return resp.fail(resp.DataQueryFail, detail=str(e))

   
       
         



    
