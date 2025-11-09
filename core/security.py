#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/22 13:20
# @Author  : CoderCharm
# @File    : security.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""
token password 验证
pip install python-jose
pip install passlib
pip install bcrypt

"""
import os
from typing import Any, Union
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
import hashlib
import bcrypt

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
        subject: Union[str, Any],
        expires_delta: timedelta = None
) -> str:
    """
    生成token
    :param subject:需要存储到token的数据(注意token里面的数据，属于公开的)
    :param expires_delta:
    :return:
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            # minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            minutes=float(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')) if os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES') else os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    # encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    encoded_jwt = jwt.encode(to_encode, os.getenv('SECRET_KEY'), algorithm=os.getenv('ALGORITHM'))
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    :param plain_password: 原密码
    :param hashed_password: hash后的密码
    :return:
    """
     # 验证时同样先进行 SHA-256 哈希
    sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    password_byte_enc = sha256_hash.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_bytes)


def get_password_hash(password: str) -> str:
    """
    获取 hash 后的密码
    :param password:
    :return:
    """
    # 先用 SHA-256 哈希密码，确保长度固定为 64 字符
    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    # 然后使用 bcrypt 哈希
    pwd_bytes = sha256_hash.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode('utf-8')
