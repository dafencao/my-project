# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# # @Time    : 2021/1/29 20:30
# # @Author  : CoderCharm
# # @File    : sys_casbin.py
# # @Software: PyCharm
# # @Github  : github/CoderCharm
# # @Email   : wg_python@163.com
# # @Desc    :
# """
# 校验casbin
# """
#
# from pydantic import BaseModel, Field
#
#
# # 创建API
# class AuthCreate(BaseModel):
#     authority_id: str
#     path: str
#     method: str
#
# # 角色权限
# class RolePerm(BaseModel):
#     role: str = Field(..., description='角色')
#     model: str = Field(..., description='模块')
#     act: str = Field(..., description='权限行为')
#
#     class Config:
#         """
#         schema_extra中设置参数的例子，在API文档中可以看到
#         """
#         schema_extra = {
#             'example': {
#                 'role': 'guest',
#                 'model': 'auth',
#                 'act': 'add'
#             }
#         }
#
#
# # 用户权限配置
# class UserPerm(BaseModel):
#     user: int = Field(..., description='用户名')
#     model: str = Field(..., description='模块')
#     act: str = Field(..., description='权限行为')
#
#     class Config:
#         """
#         schema_extra中设置参数的例子，在API文档中可以看到
#         """
#         schema_extra = {
#             'example': {
#                 'user': 'zhangsan',
#                 'model': 'user',
#                 'act': 'add'
#             }
#         }
#
#
# # 用户角色配置
# class UserRole(BaseModel):
#     user: str = Field(..., description='用户名')
#     role: str = Field(..., description='角色')
#
#     class Config:
#         """
#         schema_extra中设置参数的例子，在API文档中可以看到
#         """
#         schema_extra = {
#             'example': {
#                 'user': 'zhangsan',
#                 'role': 'guest'
#             }
#         }