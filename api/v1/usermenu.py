

from typing import Any
from datetime import timedelta, datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, Body

from common.deps import verify_current_user_perm
from common.session import get_db

from core import security
from models.usermenu import Usermenu
from common import deps, logger
from schemas.response import resp
from schemas.request import sys_usermenu_schema
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn

router = APIRouter()


@router.post("/sys/menu/add", summary="添加菜单", name="添加菜单")
async def add_usermenu_info(
    menu: sys_usermenu_schema.MenuCreate
) -> Any:
    try:
        menu.create_at = datetime.strftime(
            datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        menu_dict = dict(menu)
        result = await Usermenu.add_usermenu(menu_dict)
        return resp.ok(data=result)
        
    except Exception as e:
        return resp.fail(resp.DataInsertFail, detail=f"添加菜单失败: {str(e)}")


@router.delete("/sys/menu/delete", summary="删除菜单", name="删除菜单")
async def del_usermenu(
    id: int
) -> Any:
    try:
        result =await Usermenu.del_by_usermenu_id(id)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)


@router.delete("/sys/menu/deleteBatch", summary="批量删除菜单", name="批量删除菜单")
async def del_usermenu(
    usermenu_ids: list
) -> Any:
    try:
        # 转换为整数
        menu_ids = [int(id) for id in usermenu_ids]

        # 执行删除操作
        result = await Usermenu.del_by_usermenu_ids(menu_ids)
        
        # 检查删除结果
        if result == 0:
            return {"success": True, "code": 200, "data": result, "msg": f"成功删除 {result} 个菜单"}
        
    except Exception as e:
        return {"success": False, "code": 500, "msg": f"删除失败: {str(e)}", "data": None}


@router.put("/sys/permission/edit", summary="编辑菜单", name="编辑菜单")
async def edit_menu(
    menu: sys_usermenu_schema.MenuUpdate
) -> Any:
    menu.updateAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    print(menu)
    if menu.menuType == 1:
        menu.parentId = 0
    menu = dict_to_model(Usermenu,  dict(menu))

    try:
        result =await Usermenu.update_menu(menu)
        # result = menu.save()
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
    return resp.ok(data=result)


@router.post("/sys/permission/list", summary="查询所有菜单", name="查询所有菜单",dependencies=[Depends(verify_current_user_perm)])
async def show_user(req: sys_usermenu_schema.MenuQuery,) -> Any:

    result =await Usermenu.fuzzy_query(req)
    addList = []
    for menu in result:
        if not (menu['parentId'] == None or menu['parentId'] == 0):
            addList.append(menu['parentId'])
    # addResult = list(Usermenu.select().where(Usermenu.id.in_(addList)).dicts())
    addResult = await Usermenu.select_by_ids(addList)
    for item in addResult:
        flag = True
        for res in result:
            if item['id'] == res['id']:
                flag = False
                break
        if flag:
            result.append(item)
    # result.extend(addResult)
    # result = set(result)
    menuList = sorted(result, key=lambda e: (e.__getitem__(
        'menuType'),  e.__getitem__('sortNo')), reverse=False)
    # print(menuList)
    # menuList = result

    result = []
    for menu in menuList:
        if menu['parentId'] == None or menu['parentId'] == 0:
            temp = {}
            temp['id'] = menu['id']
            temp['url'] = menu['url']
            temp['component'] = menu['component']
            temp['name'] = menu['name']
            temp['icon'] = menu['icon']
            temp['menuType'] = menu['menuType']
            temp['sortNo'] = menu['sortNo']

            temp['children'] = []
            result.append(temp)

    # print('result')
    # print(result)
    for menu in menuList:
        if menu['parentId'] != None or menu['parentId'] != 0:
            # print(menu['name'])
            temp = {}
            temp['id'] = menu['id']
            temp['parentId'] = menu['parentId']
            temp['url'] = menu['url']
            temp['component'] = menu['component']
            temp['name'] = menu['name']
            temp['icon'] = menu['icon']
            temp['menuType'] = menu['menuType']
            temp['sortNo'] = menu['sortNo']

            # temp['menuType'] = menu['menuType']

            for menu1 in result:
                if menu1['id'] == menu['parentId']:
                    # print("menu1['id']")
                    # print(menu1)
                    menu1['children'].append(temp)
                    break
    # result = result.reverse()
    total = len(result)

    return resp.ok(data=result, total=total)
    # except Exception as e:
    #     print(e)
    #     return resp.fail(resp.DataNotFound )


@router.get("/{roleId}", summary="根据roleid筛选角色的权限", name="查询角色权限")
async def query_user_roleId(roleId: str):
    result =await  Usermenu.select_by_roleId(roleId)

    print(result)
    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="User not found")

# @router.post("/sys/permission/saveRolePermission", summary="保存角色权限", name="保存角色权限")
# def add_usermenu_info(
#         usermenu: sys_usermenu_schema.usermenuBase
# ) -> Any:
#     print("usermenu")

#     result = Usermenu.add_usermenu(usermenu)
#     return resp.ok(data=result)


#
@router.get("/sys/role/queryTreeList", summary="查询所有的菜单", name="查询所有的菜单", dependencies=[Depends(get_db)])
async def queryTreeList():
    result = {}
    db = await Usermenu.select_all()
    if db:
        menuList = list(db)
    else:
        menuList = []
    menuList = sorted(menuList, key=lambda e: (e.__getitem__(
        'menuType'),  e.__getitem__('sortNo')), reverse=False)
    result['treeList'] = []
    for menu in menuList:
        if menu['parentId'] == None or menu['parentId'] == 0:
            temp = {}
            temp['key'] = menu['id']
            temp['path'] = menu['url']
            temp['component'] = menu['component']
            temp['slotTitle'] = menu['name']
            temp['icon'] = menu['icon']

            temp['children'] = []
            result['treeList'].append(temp)
    print("result['treeList']")
    print(result['treeList'])
    for menu in menuList:
        if menu['parentId'] != None or menu['parentId'] != 0:
            temp = {}
            temp['key'] = menu['id']
            temp['path'] = menu['url']
            temp['component'] = menu['component']
            temp['slotTitle'] = menu['name']
            temp['icon'] = menu['icon']

            for menu1 in result['treeList']:
                if menu1['key'] == menu['parentId']:
                    # print("menu1['id']")
                    # print(menu1)
                    menu1['children'].append(temp)
                    break

    # print("result['treeList']")
    # print(result['treeList'])
    if result:
        return resp.ok(data=result)
    else:
        return resp.fail(resp.DataNotFound, detail=str(e))
