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
from fastapi import APIRouter, Depends, HTTPException, Form
from datetime import datetime, timedelta
from typing import Any
from schemas.response import resp
from schemas.request import sys_userrole_schema
from models.user import UserRoleRelp, Userinfo
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError

router = APIRouter()


@router.post("/sys/role/add", summary="添加角色", name="新增一条用户记录")
async def role_add(req: sys_userrole_schema.RoleCreate):
    role = dict(req)
    role['createAt'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    role['updateAt'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    role['updateBy'] = role['createBy']
    # print('role')
    # print(role)
    permList = []
    # try:
    #     result = await Permission.get_all_perm()
    # except Exception as e:
    #     return resp.fail(resp.DataStoreFail, detail=str(e))
    # for item in result:
    #     permList.append(item['id'])
    # print('permList')
    # print(permList)
    try:
        async with db.atomic_async():
            roleId =await Userrole.add_role(role)
            for id in req.permissionIds:
                # RoleMenuRelp.create(
                #     roleId=roleId,
                #     menuId=id)
                await RoleMenuRelp.add({'roleId': roleId, 'menuId': id,'createAt':role['createAt']})
            # for id in permList:
                # RolePermRelp.create(
                #     roleId=roleId,
                #     permId=id)
                # await RolePermRelp.add({'roleId': roleId, 'perm': id})

            # print('roleId')
            # print(roleId)
        return resp.ok(data=roleId)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('角色编码已存在！'))
        # return resp.ok( msg='角色编码已存在！' )

    except Exception as e:
        print(e)
        return resp.fail(resp.DataStoreFail, detail=str(e))


@router.post("/sys/role/delete/{id}", summary="删除角色", name="删除角色")
async def del_user(
        id: str
) -> Any:
    print(id)
    try:
        async with db.atomic_async():
            result =await Userrole.del_by_userroleid(id)
            # print(list(Userinfo.select().where(Userinfo.userRoleId==id).dicts()))

            await async_db.execute(Userinfo.update(userRoleId=None).where(Userinfo.userRoleId == id))
            # UserRoleRelp.delete().where(UserRoleRelp.roleId == id).execute()
            # RoleMenuRelp.delete().where(RoleMenuRelp.roleId == id).execute()
            # RolePermRelp.delete().where(RolePermRelp.roleId == id).execute()
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
    print('show req')
    print(req)
    item_dict = dict(req)
    try:
        result =await  Userrole.fuzzy_query(req)
        # print('这是全部角色')
        # print(result)
        # print(len(result))
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
    pass


@router.get("/sys/role/queryById", summary="根据id查看角色详细信息", name="查询角色详情")
async def query_user_id(id: str):
    result =await  Userrole.select_by_id(id)
    print(result)
    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="User not found")


@router.get("/sys/permission/queryRolePermission/{roleId}", summary="根据id查看角色详细信息", name="查询角色详情")
async def queryRolePermission(roleId: int):
    result = await  RoleMenuRelp.select_by_role_id(roleId)
    print('result')
    print(result)
    if result:
        return resp.ok(data=result)
    else:
        result = {
            'menuIds': [],
            'roleId': roleId
        }
        return resp.ok(data=result)

    #     raise HTTPException(
    #         status_code=404, detail="role not found")


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

