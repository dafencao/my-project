'''
Author: 嘉欣 罗 2592734121@qq.com
Date: 2022-12-22 12:49:07
LastEditors: Please set LastEditors
LastEditTime: 2023-05-10 11:19:08
FilePath: \psad-backend\schemas\response\resp.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/9/22 13:32
# @Author  : CoderCharm
# @File    : response_code.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""

统一响应状态码

"""




import string
from typing import Union
from fastapi import status as http_status
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from utils.tools_func import name_convert_to_camel
class Resp(object):
    def __init__(self, status: int, msg: str, code: int):
        self.status = status
        self.msg = msg
        self.code = code

    def set_msg(self, msg):
        self.msg = msg
        return self


Unauthorized: Resp = Resp(401, "用户没有权限（令牌、用户名、密码错误）。",
                          http_status.HTTP_401_UNAUTHORIZED)
Timeout: Resp = Resp(408, "请求超时，请稍后重试哦。",
                          http_status.HTTP_408_REQUEST_TIMEOUT)
InvalidRequest: Resp = Resp(1000, "无效的请求", http_status.HTTP_400_BAD_REQUEST)
InvalidParams: Resp = Resp(1002, "无效的参数", http_status.HTTP_400_BAD_REQUEST)
BusinessError: Resp = Resp(1003, "业务错误", http_status.HTTP_400_BAD_REQUEST)
DataNotFound: Resp = Resp(1004, "查询失败", http_status.HTTP_400_BAD_REQUEST)
DataStoreFail: Resp = Resp(1005, "新增失败", http_status.HTTP_400_BAD_REQUEST)
DataUpdateFail: Resp = Resp(1006, "更新失败", http_status.HTTP_400_BAD_REQUEST)
DataDestroyFail: Resp = Resp(1007, "删除失败", http_status.HTTP_400_BAD_REQUEST)
PermissionDenied: Resp = Resp(1008, "权限拒绝", http_status.HTTP_403_FORBIDDEN)
ServerError: Resp = Resp(
    5000, "服务器繁忙", http_status.HTTP_500_INTERNAL_SERVER_ERROR)


def ok(*, data: Union[list, dict, str] = None, total: int = None, msg: str = "success", success=True) -> Response:
    # print('ok1')

    # data = explain(data)

    # print('ok2')
    return JSONResponse(
        status_code=http_status.HTTP_200_OK,


        content=jsonable_encoder({
            'status': 200,
            "success": success,
            'msg': msg,
            'data': data,
            'total': total
        })
    )


def fail(resp: Resp, detail: str = None) -> Response:
    return JSONResponse(
        status_code=resp.code,
        content=jsonable_encoder({
            'status': resp.status,
            'msg': resp.msg,
            "success": False,
            'detail': detail,
        })
    )


def explain(data: Union[list, dict, str]):
    if (isinstance(data, list)):
        for d in data:
            originKeys = []
            newKeys = []
            # print('d:')
            # print(d)
            if (isinstance(d, dict)):
                for key in d:
                    originKeys.append(key)

                    newKey = name_convert_to_camel(key)
                    newKeys.append(newKey)

            # print(originKeys)
            # print(newKeys)
            for i in range(0, len(originKeys)):
                # print(i)
                d[newKeys[i]] = d.pop(originKeys[i])

    elif (isinstance(data, dict)):

        # print('dict2')
        originKeys = []
        newKeys = []
        for key in data:
            if (isinstance(data[key], dict)):
                temp = {}
                for i in data[key].keys():
                    temp[name_convert_to_camel(i)] = data[key][i]
                data[key] = temp
            # print("###key:"+key)
            originKeys.append(key)
            newKey = name_convert_to_camel(key)
            newKeys.append(newKey)
        for i in range(len(originKeys)):
            data[newKeys[i]] = data.pop(originKeys[i])

    return data
