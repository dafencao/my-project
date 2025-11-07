from typing import Any, List, Optional
from datetime import datetime, timedelta

import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, Header

from core import security

from models.user import Department, Level, UserLineRelp, UserPostRelp, UserRoleRelp, Userinfo, Userline, Userpost

from common import deps, logger
from models.usermenu import Usermenu
from models.userrole import RoleMenuRelp, Userrole
from schemas.response import resp
from schemas.request import sys_userinfo_schema
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError
from logic.user_logic import UserInfoLogic
from schemas.request import sys_user_schema
from common.session import db, get_db
from utils.tools_func import rolePremission, tz


router = APIRouter()


@router.post("/login", summary="用户登录认证", name="登录")
async def login_access_token(
        req: sys_user_schema.UserAuth,
) -> Any:
    """
    简单实现登录
    :param req:
    :return:
    """

    # 验证用户 简短的业务可以写在这里
    # if not user:
    #     return resp.fail(resp.DataNotFound.set_msg("账号或密码错误"))
    #
    # if not security.verify_password(req.password, user.password):
    #     return resp.fail(resp.DataNotFound.set_msg("账号或密码错误"))
    #
    # access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    #
    # # 登录token 存储了user.id
    # return resp.ok(data={
    #     "token": security.create_access_token(user.id, expires_delta=access_token_expires),
    # })

    # 复杂的业务逻辑建议 抽离到 logic文件夹下
    # result =await UserInfoLogic().user_login_logic(req.account, req.password)
    # if result:
    #     return resp.ok(data={"token": result})
    # else:
    #     return resp.fail(resp.Unauthorized.set_msg("账号或密码错误"))
    print("=== 登录请求开始 ===")
    print(f"请求数据: account={req.account}, password_length={len(req.password) if req.password else 0}")
    try:
        # 参数验证
        if not req.account or not req.account.strip():
            return resp.fail(resp.InvalidParams.set_msg("账号不能为空"))
        
        if not req.password or not req.password.strip():
            return resp.fail(resp.InvalidParams.set_msg("密码不能为空"))
        
        print(f"🔍 参数验证通过，开始调用业务逻辑")
        # 调用业务逻辑处理登录
        result = await UserInfoLogic().user_login_logic(req.account, req.password)
        
        if result:
            return resp.ok(data={"token": result})
        else:
            return resp.fail(resp.Unauthorized.set_msg("账号或密码错误"))
            
    except Exception as e:
        print(f"❌ 登录过程发生异常:")
        print(f"   异常类型: {type(e).__name__}")
        print(f"   异常信息: {str(e)}")
        print(f"   请求账号: {req.account}")
        # 捕获其他所有异常
        print(f"登录系统异常: {e}")


        import traceback
        tb_info = traceback.format_exc()
        print(f"   完整堆栈:\n{tb_info}")
        
    


@router.get("/currentUser", summary="获取用户信息", name="获取用户信息")
async def get_current_user(
        *,
        current_user: Userinfo = Depends(deps.get_current_userinfo),
        # Referer: dict = Depends(deps.save_user_action)

) -> Any:
    current_user.pop('password')
    result =await Userrole.query_role_perm(current_user['userRoleId'])
    # current_user['allAuth'] = rolePremissionList[current_user['userRoleId']]
    current_user['allAuth'] = result

    return resp.ok(data=current_user)


# /sys/add
@router.post("/add", summary="新增一条用户记录", name="添加用户")
async def add_userinfo_info(
        userinfo: sys_user_schema.UserCreate,
) -> Any:
    userinfo.createAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    userinfo.updateAt = userinfo.createAt
    # print("user")
    # print(userinfo)
    userinfo.password = security.get_password_hash(userinfo.password)
    user = userinfo.dict()
    try:
        async with db.atomic_async():

            result =await Userinfo.add_user(user)
            # print('result')
            # print(result)
            # 同步更新用户角色关系表 即搜索关系表得到的selectedRoles字段
            await UserRoleRelp.add(
                {'userId': result, 'roleId': userinfo.userRoleId})
            # 同步更新用户产品线关系表
            if userinfo.line:
                for lineId in userinfo.line:
                    # UserLineRelp.create(
                    #     userId=result, lineId=lineId)
                    await UserLineRelp.add({'userId': result, 'lineId': lineId})
            # 同步更新用户职位关系表
            if userinfo.post:

                for postId in userinfo.post:
                    await UserPostRelp.add({
                        'userId': result, 'postId': postId})

    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('用户账号已存在！'))

    except Exception as e:
        # print(e)
        # print(type(e))
        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok(data=result)


@router.post("/add/list", summary="新增多条用户记录", name="添加用户")
async def add_userinfo_info(
        userList: List[sys_user_schema.UsersCreate],
) -> Any:
    importField = 'code'
    roleCodeDict = {}
    result =await Userrole.select_all()
    for item in result:
        roleCodeDict[item['roleCode']] = item['id']
    print('roleCodeDict')
    print(roleCodeDict)
    departmentDict = {}
    # result = list(Department.select().dicts())
    result = await Department.select_all()
    for item in result:
        departmentDict[item[importField]] = item['id']

    postDict = {}
    result = await Userpost.select_all()
    for item in result:
        postDict[item[importField]] = item['id']
    lineDict = {}
    result =await Userline.select_all()
    for item in result:
        lineDict[item[importField]] = item['id']
    levelDict = {}
    result = await Level.select_all()
    for item in result:
        levelDict[item[importField]] = item['id']
    for userinfo in userList:
        print(userinfo.birthday)
        print(type(userinfo.birthday))
        # userinfo.phone = userinfo.phone.group()
        # try:
        #     print(userinfo.birthday)
        #     print(type(userinfo.birthday))
        #     userinfo.birthday = datetime.strptime(userinfo.birthday, "%Y-%m-%dT%H:%M:%S.%f%z")
        # except Exception as e:
        #     return resp.fail(resp.DataStoreFail.set_msg('生日日期格式错误'+ userinfo.birthday+'， 请检查！'))

        # print("user")
        # print(userinfo.roleCode)
        userinfo.password = security.get_password_hash(userinfo.password)
        user = userinfo.dict()
        # user['createAt'] = datetime.strftime(
        #             datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        if userinfo.department not in departmentDict.keys():
            return resp.fail(resp.DataStoreFail.set_msg('部门编码 ' + userinfo.department + '不存在，请检查！'))
        user['oraCode'] = departmentDict[userinfo.department]
        if userinfo.level not in levelDict.keys():
            return resp.fail(resp.DataStoreFail.set_msg('技术层级编码' + userinfo.level + '不存在，请检查！'))
        user['level'] = levelDict[userinfo.level]
        if userinfo.roleCode not in roleCodeDict:
            return resp.fail(resp.DataStoreFail.set_msg('角色编码' + userinfo.roleCode + '不存在，请检查！'))
        user['userRoleId'] = roleCodeDict[userinfo.roleCode]
        if userinfo.post:
            for post in userinfo.post:
                if post not in postDict.keys():
                    return resp.fail(resp.DataStoreFail.set_msg('职位信息与数据库不匹配！' + post))
                else:
                    post = postDict[post]
        if userinfo.line:
            for line in userinfo.line:
                if line not in lineDict.keys():
                    return resp.fail(resp.DataStoreFail.set_msg('产品线信息与数据库不匹配！' + line))
                else:
                    line = lineDict[line]
        print('user')
        print(user)
        user['createAt'] = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        user['updateAt'] = datetime.strftime(
            datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        # print('userinfo')
        # print(userinfo)
        # print(roleDict.keys())
        try:
            async with db.atomic_async():
                # 字段有效
                result =await Userinfo.add_user(user)
                # print('result')
                # print(result)
                # 同步更新用户角色关系表 即搜索关系表得到的selectedRoles字段
                await UserRoleRelp.add(
                    {'userId': result, 'roleId': roleCodeDict[userinfo.roleCode]})
                # 同步更新用户产品线关系表
                if userinfo.line:
                    for line in userinfo.line:
                        # UserLineRelp.create(
                        #     userId=result, lineId=lineDict[line])
                        await UserLineRelp.add({'userId': result, 'lineId': lineDict[line]})

                # 同步更新用户职位关系表
                if userinfo.post:

                    for post in userinfo.post:
                        await UserPostRelp.add(
                            {'userId': result, 'postId': postDict[post]})
        except IntegrityError as e:
            return resp.fail(resp.DataStoreFail.set_msg('用户账号已存在！'), detail=str(e))
            # return resp.ok(data=[], msg='用户账号已存在！', success=False)

        except Exception as e:
            print(e)
            return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok()


# , dependencies= [Depends(get_db)]
@router.delete("/delete", summary="删除一条用户信息", name="删除用户")
async def del_user(
        id: str
) -> Any:
    # print(id)
    try:
        async with db.atomic_async():
            result =await Userinfo.del_by_userid(id)
            await UserRoleRelp.delete_by_userId(id)
            await UserLineRelp.delete_by_userId(id)
            await UserPostRelp.delete_by_userId(id)
            # UserLineRelp.delete().where(UserLineRelp.userId == id)
    except Exception as e:
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)


# /sys/edit


@router.put("/update", summary="修改一条用户记录", name="编辑用户")
async def edit_user(
        # userinfo: dict  修改与添加大同小异 修改没有password字段
        req: sys_user_schema.UserUpdate,
) -> Any:
    req.updateAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    userRoleId = req.userRoleId
    userId = req.id
    # TODO:userRoleId
    # print('req.updateAt')
    # print(req.updateAt)
    # print('dict(req)')
    # print(dict(req))

    lastUserInfo =await Userinfo.select_by_id(req.id)
    # print('lastUserInfo')
    # print(lastUserInfo)
    user = dict(req)
    user.pop('line')
    user.pop('post')
    user = dict_to_model(Userinfo, user)
    # try:
    if True:
        async with db.atomic_async():
            result =await Userinfo.update_user(user)
            if lastUserInfo['userRoleId'] != req.userRoleId:
                # result = list(UserRoleRelp.select().where(UserRoleRelp.userId == req.userRoleId).dicts())
                result = await UserRoleRelp.select_by_userId(req.userRoleId)
                if len(result) == 0:
                    print("##########################")
                    print(req)
                    data_dict = {'roleId': req.userRoleId, 'userId': req.id, 'updateAt': datetime.strftime(
                        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')}
                    await UserRoleRelp.add(data_dict)
                else:
                    # UserRoleRelp.update({UserRoleRelp.roleId: userinfo.userRoleId}).where(
                    #     UserRoleRelp.userId == userinfo.id).execute()
                    UserRoleRelp.update({'roleId': req.userRoleId}).where(
                        UserRoleRelp.userId == userId).execute()
                    relp = dict_to_model(UserRoleRelp, {'userId': userId, 'roleId': req.userRoleId})
                    await UserRoleRelp.update_by_model(relp)

            if req.line and lastUserInfo['lineIds'] != req.line:

                # print('!=')
                for id in req.line:
                    if id not in lastUserInfo['lineIds']:
                        # print('create')
                        # UserLineRelp.create(
                        #     userId=userId,
                        #     lineId=id)
                        await UserLineRelp.add({'userId': userId,
                                                'lineId': id})
                for id in lastUserInfo['lineIds']:
                    if id not in req.line:
                        # print('delete')
                        # result = UserLineRelp.delete().where(UserLineRelp.lineId ==
                        #                                      id, UserLineRelp.userId == userId).execute()
                        result = UserLineRelp.delete_by_userId_and_lineId(userId, id)
            if req.post and lastUserInfo['postIds'] != req.post:
                for id in req.post:
                    if id not in lastUserInfo['postIds']:
                        await UserPostRelp.add(
                            {'userId': userId,
                             'postId': id})
                for id in lastUserInfo['postIds']:
                    if id not in req.post:
                        # result = UserPostRelp.delete().where(UserPostRelp.postId ==
                        #                                      id, UserPostRelp.userId == userId).execute()
                        await UserPostRelp.delete_by_userId_and_postId(userId, id)
        return resp.ok( )
    # except Exception as e:
    #     print(e)
    #     return resp.fail(resp.DataUpdateFail, detail=str(e))


# /sys/list,
#
@router.post("/show", summary="根据条件筛选用户记录", name="查询用户列表", dependencies=[Depends(get_db)])
async def show_user(queryuserinfo: sys_user_schema.UserQuery) -> Any:
    # print('show queryuserinfo')
    # print(queryuserinfo)
    item_dict = dict(queryuserinfo)
    try:
        result =await Userinfo.fuzzy_query(queryuserinfo)
        # print('result')
        # print(result)
        total = len(result)
        result = result[(queryuserinfo.current - 1) *
                        queryuserinfo.pageSize:(queryuserinfo.current) * queryuserinfo.pageSize]
        return resp.ok(data=result, total=total)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    pass


@router.get("/get/{id}", summary="根据id查看用户详细信息", name="获取用户信息")
async def query_user_id(id: str):
    result =await Userinfo.select_by_id(id)
    # result = User.get_user_by_id(1)
    result.pop('password')
    result.pop('createAt')
    result.pop('updateAt')
    # print(result)
    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="User not found")


@router.post("/role", summary="根据id查看用户角色信息", name="获取用户信息")
async def query_user_id(id: int):
    result =await Userinfo.select_user_role(id)
    # result = User.get_user_by_id(1)
    # print(result)
    if result:
        return resp.ok(data=result)
    else:
        raise HTTPException(
            status_code=404, detail="User not found")


# TODO
@router.put("/sys/updatePassword", summary="修改用户密码", name="修改用户密码")
async def update_password(req: sys_user_schema.UserUpdatePwd,
                    # current_user: Userinfo = Depends(deps.get_current_userinfo)
                    ) -> Any:
    req.updateAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    current_user =await Userinfo.single_by_account(req.account)
    # print('current_user')
    # print(current_user)
    oldHashedPassword = current_user['password']
    oldpassword = req.oldPassword
    if not security.verify_password(oldpassword, oldHashedPassword):
        return resp.fail(resp.DataUpdateFail.set_msg("密码错误"))
    req.password = security.get_password_hash(req.password)
    item_dict = {
        'id': current_user['id'],
        'account': current_user['account'],
        'password': req.password
    }
    user = dict_to_model(Userinfo, item_dict)
    try:
        result = user.save()
    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok(data=result)


@router.put("/sys/changePassword", summary="管理员修改用户密码", name="管理员修改用户密码")
def update_password(req: sys_user_schema.UserUpdatePwd,
                    # current_user: Userinfo = Depends(deps.get_current_userinfo)
                    ) -> Any:
    req.updateAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    # print('current_user')
    # print(current_user)
    # password = current_user["password"]
    # account = current_user["account"]
    password = security.get_password_hash(req.password)
    # print('password')
    # print(password)

    item_dict = {
        'id': req.id,
        'account': req.account,
        'password': password,
    }
    user = dict_to_model(Userinfo, item_dict)

    try:
        result = user.save()
    except Exception as e:
        print(e)
        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok(data=result)


@router.get("/sys/permission/getUserPermissionByToken", summary="获取账户菜单信息", name="获取账户菜单信息",
            dependencies=[Depends(get_db)])
async def get_user_permission_by_token(
        *,
        current_userinfo: Userinfo = Depends(deps.get_current_userinfo),
) -> Any:
    # current_userinfo.pop('password')
    # 获取权限信息
    # print("获取权限信息")
    # TODO:获取账户菜单信息 格式处理
    # user=>role
    # print(current_userinfo)
    role = current_userinfo['userRoleId']
    # role = current_userinfo['selectedRoles']
    result =await RoleMenuRelp.select_by_role_id(role)
    menuIds = result['menuIds']
    menuList =  await Usermenu.select_by_ids(menuIds)
    # print(menuList)
    menuList = sorted(menuList, key=lambda e: (e.__getitem__(
        'menuType'), e.__getitem__('sortNo')), reverse=False)
    # print(menuList)

    result = {}
    result['menu'] = []
    for menu in menuList:
        if menu['parentId'] == None or menu['parentId'] == 0:
            temp = {}
            temp['id'] = menu['id']
            temp['path'] = menu['url']
            temp['component'] = menu['component']
            temp['meta'] = {
                'icon': menu['icon'],
                'keepAlive': menu['keepAlive'],
                'title': menu['name'],
            }
            temp['children'] = []
            result['menu'].append(temp)
    # print("result['menu']")
    # print(result['menu'])
    for menu in menuList:
        if (menu['parentId'] != None or menu['parentId'] != 0) and menu['menuType'] != 0:
            temp = {}
            temp['id'] = menu['id']
            temp['path'] = menu['url']
            temp['component'] = menu['component']
            temp['meta'] = {
                'icon': menu['icon'],
                'keepAlive': menu['keepAlive'],
                'title': menu['name'],
            }
            for menu1 in result['menu']:
                if menu1['id'] == menu['parentId']:
                    # print("menu1['id']")
                    # print(menu1)
                    menu1['children'].append(temp)
                    break

    return resp.ok(data=result)


#
@router.get("/level", summary="获取职级信息", name="获取职级信息", dependencies=[Depends(get_db)])
async def get_level() -> Any:
    result = await Level.select_all()

    return resp.ok(data=result)


# *lru_cache
# https://www.cnblogs.com/lifei01/p/14105346.html
@router.get("/line", summary="获取产品线信息", name="获取产品线信息", dependencies=[Depends(get_db)])
async def get_line() -> Any:
    result = await Userline.select_all()

    return resp.ok(data=result)


#
@router.get("/post", summary="获取职位信息", name="获取职位信息", dependencies=[Depends(get_db)])
async def get_post() -> Any:
    result = await Userpost.select_all()

    return resp.ok(data=result)


#
@router.get("/department", summary="获取部门信息", name="获取账户菜单信息", dependencies=[Depends(get_db)])
async def get_department() -> Any:
    # db = Department.select(Department.id, Department.name).dicts()
    result = await Department.select_all()

    return resp.ok(data=result)


