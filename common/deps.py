#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/16 11:51
# @Author  : CoderCharm
# @File    : deps.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""

一些通用的依赖功能

"""
import os
from datetime import datetime
from typing import Any, Union, Optional

import pytz
#
from jose import jwt
from fastapi import Header, Depends, Request, HTTPException
from pydantic import ValidationError

from common import custom_exc
from core.config import settings
from models.user import Userinfo
from models.user_action import User_action
from models.usermenu import Usermenu
from models.userrole import Userrole, RoleMenuRelp
from schemas.response import resp
from utils.tools_func import tz


def check_authority(token: Optional[str] = Header(..., description="登录token")):
    return


def get_request_info(
        request: Request,
) -> Any:
    # print('-----get_request_info------')
    # print(dict(request))
    # print('request.client.host')
    # print(request.client.host)
    hs = request.headers
    # print('hs')
    # print(hs)
    ip = hs.get('x-real-ip')
    account = ''
    token = hs.get("token")
    host = hs.get("host")

    if token != None:
        # 解析token。将id从token中解析出来去。
        try:
            payload = jwt.decode(
                token,
                # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                os.getenv('SECRET_KEY'), algorithms = [os.getenv('ALGORITHM')]
            )
        except jwt.ExpiredSignatureError as e:
            # TODO token续期
            print('登录已经过期')
            raise resp.fail(resp.Unauthorized.set_msg('登录已经过期.'))
        except Exception as e:
            return resp.fail(resp.Unauthorized.set_msg('登录失败，请重试。'), detail=str(e))

        account = payload.get("sub")
        info = {
            'token': token,
            'account': account,
            'host': host,
            'ip': ip
        }
        return info
    return


def check_jwt_token(
        token: Optional[str] = Header(..., description="登录token")
) -> Union[str, Any]:
    """
    解析验证token  默认验证headers里面为token字段的数据
    可以给 headers 里面token替换别名, 以下示例为 X-Token
    token: Optional[str] = Header(None, alias="X-Token")
    :param token:
    :return:
    """
    try:
        payload = jwt.decode(
            token,
            # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')]
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        print(e)
        print(str(e))
        raise custom_exc.TokenAuthError()
        # return resp.fail(resp.Unauthorized.set_msg('登陆已过期，请重新登陆'))
    except (jwt.JWTError, ValidationError, AttributeError):
        raise custom_exc.TokenAuthError()
        # return resp.fail(resp.Unauthorized.set_msg('用户验证失败'))





async def get_current_userinfo(
        token: Optional[str] = Depends(check_jwt_token)
) -> Userinfo:
    """
    根据header中token 获取当前用户
    :param db:
    :param token:
    :return:
    """
    # print(token.get("sub"))
    user = await Userinfo.single_by_account(account=token.get("sub"))
    if not user:
        # return resp.fail(resp.d)
        raise HTTPException(status_code=401, detail="未找到用户信息。")
        # raise custom_exc.TokenExpired(err_desc="未找到用户信息。")
    return user


async def get_current_user_perm(
        token: Optional[str] = Depends(check_jwt_token)
) -> Userinfo:
    """
    根据header中token 获取当前用户permission
    :param db:
    :param token:
    :return:
    """
    # print(token.get("sub"))
    user =await Userinfo.single_by_account(account=token.get("sub"))
    print(user)
    if not user:
        raise HTTPException(status_code=401, detail="未找到用户信息。")
    result =await Userrole.query_role_perm(user['userRoleId'])
    # rolePremissionList = {}
    # for item in result:
    #     rolePremissionList[item['id']] = item['perm']
    # print('Userrole.query_role_perm()')

    # print(rolePremissionList)
    # print(user['userRoleId'])
    # print(rolePremissionList[user['userRoleId']])
    user['allAuth'] = result
    if user['allAuth']:
        return user['allAuth']
    return []


async def verify_current_user_perm(
        # current_perm:str,
        token: Optional[str] = Depends(check_jwt_token)
) -> Any:
    """
    根据header中token 获取当前用户permission
    :param db:
    :param token:
    :return:
    """
    # print(token.get("sub"))
    user =await Userinfo.single_by_account(account=token.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="未找到用户信息。")
    result = await RoleMenuRelp.select_by_role_id(user['userRoleId'])
    print('RoleMenuRelp result')
    print(result)
    menuIds = result['menuIds']
    result =await Userrole.query_role_perm(user['userRoleId'])
    print('result')
    print(result)
    menuList = await Usermenu.select_by_ids(menuIds)
    print('menuList')
    print(menuList)
    urlList = []
    for menu in menuList:
        urlList.append(menu['url'])
    # user['allAuth'] = result
    return None
    # return current_perm in result
    # if user['allAuth']:
    #     return user['allAuth']
    # return []