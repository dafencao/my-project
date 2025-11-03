'''
Descripttion: 
version: 
Author: congsir
Date: 2023-02-13 14:10:09
LastEditors: Please set LastEditors
LastEditTime: 2023-05-10 14:52:10
'''
import os
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 业务逻辑多了就写在这里

from datetime import timedelta
from common.sys_redis import redis_client

from models.user import Userinfo
from schemas.response import resp
from core import security
from core.config import settings
from common import custom_exc
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserInfoLogic(object):

    @staticmethod
    async def user_login_logic(account: str, password: str):
        account = account
        user =await Userinfo.single_by_account(account)
        # print('1111account')
        # print(account)
        print('1111user')
        print(user)
        if not user:
            raise custom_exc.TokenAuthError(err_desc="账号不存在")
        if not security.verify_password(password, user['password']):
            raise custom_exc.TokenAuthError(err_desc="密码错误")

        access_token_expires = timedelta(
            # minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            minutes=float(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))) if os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES') else os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
        token = security.create_access_token(
            user['account'], expires_delta=access_token_expires)
        # 使用token和redis怎样判断账户是否失效和异地登录
        # 将token作为value，账户的id作为key
        # 每次登录都去redis中查询该账户的登录是否过期，没有过期则删掉原来的id，token，将新生成token作为value存入redis中。过期则没有该账户信息，则重新存入redis中

        # 用户每次请求接口都需要验证是否在登录状态。（这里需要一个filter或则intercepter）获取token。解析token。将id从token中解析出来去。然后将用户的id作为key去redis中查询token。

        # 查询为空则表示登录过期。不为空则将解析出来的token和redis中的token作对比，如果相同，则用户状态正常则继续请求接口。如果不相同，则账号在其他设备登录.
        # ex 过期秒数*60*24*8
        redis_client.set(user['account'], token, ex=60*60*24*8)
        return token

    def xxx_logic(self):
        pass
