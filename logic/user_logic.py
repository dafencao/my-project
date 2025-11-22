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
from typing import Optional


from models.user import Userinfo
from schemas.response import resp
from core import security
from core.config import settings
from common import custom_exc
from passlib.context import CryptContext
from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from common import deps

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 定义 OAuth2 方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class UserInfoLogic(object):

    @staticmethod
    async def user_login_logic(account: str, password: str):
        user = await Userinfo.single_by_account(account)
        if not user:
            raise HTTPException(status_code=401, detail="账号不存在")
        if not security.verify_password(password, user['password']):
            raise HTTPException(status_code=401, detail="密码错误")

        access_token_expires = timedelta(
            minutes=float(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))) if os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES') else os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
        
        token = security.create_access_token(
            user['account'], expires_delta=access_token_expires)
        
        # 登录状态管理逻辑
        user_key = f"user:{user['user_id']}"
        
        # 检查是否已有登录状态
        existing_token = redis_client.get(user_key)
        
        if existing_token:
            # 清除旧的token映射
            old_token_key = f"token:{existing_token}"
            redis_client.delete(old_token_key)
            redis_client.delete(user_key)
            
        # 存储新的token到Redis
        redis_client.set(user_key, token, ex=60*60*24*8)
        
        # 同时存储account到token的映射
        token_key = f"token:{token}"
        redis_client.set(token_key, user['account'], ex=60*60*24*8)
        
        return token
    

async def get_current_user_for_logout(
    token: Optional[str] = Depends(deps.check_jwt_token)
) -> dict:
    """
    专门用于登出的用户获取函数
    返回包含用户信息和token的字典
    """
    # 获取用户信息
    user = await Userinfo.single_by_account(account=token.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="未找到用户信息。")
    
    # 返回包含用户信息和原始token的字典
    return {
        'user_info': user,
        'token': token  # 这里假设token是原始token字符串，如果不是请调整
    }
