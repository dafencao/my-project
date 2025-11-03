#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/15 16:57
# @Author  : CoderCharm
# @File    : custom_exc.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""
自定义异常
"""


class TokenAuthError(Exception):
    def __init__(self, err_desc: str = "用户验证失败"):
        self.err_desc = err_desc


class TokenExpired(Exception):
    def __init__(self, err_desc: str = "登陆过期"):
        self.err_desc = err_desc


class AuthenticationError(Exception):
    def __init__(self, err_desc: str = "权限被拒绝"):
        self.err_desc = err_desc

