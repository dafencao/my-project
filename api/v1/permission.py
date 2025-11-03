'''
Descripttion: 
version: 
Author: congsir
Date: 2023-03-07 10:47:39
LastEditors: 
LastEditTime: 2023-04-27 11:00:22
'''
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Form
from schemas.response import resp

router = APIRouter()


@router.get("/getUserPermissionByToken", summary="查询用户拥有的菜单信息，登录时调用", name="")
def get_user_permission_by_token(token: str, Referer: str) -> Any:
    # print('token')
    # print(token)
    print('Referer')
    print(Referer)
    result = []

    result.menu = [{
        'id': 'id',
        'path': '/overview',

        'component': './overview',
        'meta': {
            'icon': 'HomeOutlined',
            'keepAlive': False,
            'title': '产品总览',
        },
    },

        {
        'id': 'id',
        'path': '/fan/:activeKey',
        'component': './fan',
        'meta': {
            'icon': 'RadarChartOutlined',
            'keepAlive': False,
            'title': '风机选型',
        },
    },
        {
        'id': 'id',
        'path': '/system',
        'component': './system',
        'meta': {
            'icon': 'RadarChartOutlined',
            'keepAlive': False,
            'title': '系统管理',
        },
        'children': [
            {
                'id': 'id',
                'component': './system/UserList',
                'path': '/system/UserList',
                'meta': {
                    'keepAlive': False,
                    'title': '用户管理',
                },
            },
            {
                'id': 'id',
                'component': './system/RoleList',
                'path': '/system/RoleList',
                'meta': {
                    'keepAlive': False,
                    'title': '用户角色',
                },
            },
            {
                'id': 'id',
                'component': './system/MenuList',
                'path': '/system/MenuList',
                'meta': {
                    'keepAlive': False,
                    'title': '菜单管理',
                },
            },
        ],
    }]
    result.allAuth = ['/overview', '/system/MenuList',]
    result.auth = ['auth']

    return resp.ok(data=result)
