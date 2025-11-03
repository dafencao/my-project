#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/15 16:24
# @Author  : CoderCharm
# @File    : server.py.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""
包导入的时候最好遵循包导入顺序原则

标准库
第三方库
项目自定义
"""
import asyncio
import os
import threading
import time
import traceback
from typing import Optional

from fastapi import Depends, FastAPI, Header, Request, Response, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from jose import JWTError
from starlette.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ValidationError
from starlette.responses import JSONResponse, StreamingResponse

# from auth.auth import OAuth2CustomJwt
from common.deps import check_jwt_token, get_current_userinfo, get_current_user_perm
from jose import jwt

from common.sys_kafka import kafka_client
from core.config.config import Settings
from models.user import Userinfo
from models.usermenu import Usermenu
from models.userrole import Userrole, RoleMenuRelp
from router.v1_router import api_v1_router
from core.config import settings
from common.logger import logger
from common import custom_exc
# from common.sys_schedule import schedule
from common.sys_redis import redis_client
from common.session import db, get_db, async_db
from schemas.response import resp
import base64
import binascii

import casbin

from fastapi import FastAPI
from starlette.authentication import AuthenticationBackend, AuthenticationError, SimpleUser, AuthCredentials
from starlette.middleware.authentication import AuthenticationMiddleware

from fastapi_authz import CasbinMiddleware


# print("os.getenv('DOCS_URL')")
# print(os.getenv('DOCS_URL'))
def key_match(key1: str, key2: str) -> bool:
    return key1 == key2


def KeyMatchFunc(key1: str, key2: list) -> bool:
    # print('key1')
    # print(key1)
    # print('key2')
    # print(key2)
    # print('key1 in key2')
    # print(key1 in key2)
    if key1 == 'anonymous':
        return False
    return key1 in key2


import asyncio


def create_app() -> FastAPI:
    """
    生成FatAPI对象
    :return:
    """
    # print(os.getenv('DEBUG'))
    debug = True if os.getenv('DEBUG') == 'True' else False
    app = FastAPI(
        # debug=settings.DEBUG,
        debug=debug,
        title=os.getenv('TITLE') if debug else None,
        description=os.getenv('DESCRIPTION') if debug else None,
        docs_url=os.getenv('DOCS_URL') if debug else None,
        openapi_url=os.getenv('OPENAPI_URL') if debug else None,
        redoc_url=os.getenv('REDOC_URL') if debug else None,
        dependencies=[Depends(get_db)]

        # dependencies=[Depends(OAuth2CustomJwt(tokenUrl="/user/login"))]
    )

    class BasicAuth(AuthenticationBackend):
        async def authenticate(self, request):
            if "token" not in request.headers:
                return None

            token = request.headers["token"]
            # 解析token。将id从token中解析出来去。
            try:
                payload = jwt.decode(
                    token,
                    # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                    os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')]
                )
            except jwt.ExpiredSignatureError as e:
                # TODO token续期
                print('登录已经过期')
                return resp.fail(resp.Unauthorized.set_msg('登录已经过期.'))
                # raise custom_exc.TokenExpired()
            except Exception as e:
                return resp.fail(resp.Unauthorized.set_msg('登录失败，请重试。'), detail=str(e))
            account = payload.get("sub")

            try:
                user = await Userinfo.single_by_account(account)
                permList = await get_current_user_perm(payload)
                result = await RoleMenuRelp.select_by_role_id(user['userRoleId'])
                print('RoleMenuRelp result')
                print(result)
                menuIds = result['menuIds']

                menuList = await Usermenu.select_by_ids(menuIds)
                urlList = []
                for menu in menuList:
                    urlList.append(menu['url'])
            except (ValueError, UnicodeDecodeError, binascii.Error):
                raise AuthenticationError("Invalid basic auth credentials")
            username = '"'.join(permList) + '"' + '"'.join(urlList) + '"' + '/api/docs/"'
            print(('user'))
            print((user))
            # username = user

            print(('username'))
            print((username))
            # username, _, password = decoded.partition(":")
            return AuthCredentials(["authenticated"]), SimpleUser(username)

    # enforcer = casbin.Enforcer('./casbin/model.conf', './casbin/policy.csv')
    # enforcer.add_function('my_func', KeyMatchFunc)
    # app.add_middleware(CasbinMiddleware, enforcer=enforcer)
    # app.add_middleware(AuthenticationMiddleware, backend=BasicAuth())

    # 其余的一些全局配置可以写在这里 多了可以考虑拆分到其他文件夹

    # 跨域设置
    register_cors(app)

    # 注册路由
    register_router(app)

    # 注册捕获全局异常
    register_exception(app)

    # 请求拦截
    register_hook(app)

    # 取消挂载在 request对象上面的操作，感觉特别麻烦，直接使用全局的
    register_init(app)

    # if settings.DEBUG:
    if bool(os.getenv('DEBUG')) if os.getenv('DEBUG') else os.getenv('DEBUG'):
        # 注册静态文件
        register_static_file(app)

    return app


def register_static_file(app: FastAPI) -> None:
    """
    静态文件交互开发模式使用
    生产使用 nginx 静态资源服务
    这里是开发是方便本地
    :param app:
    :return:
    """
    import os
    from fastapi.staticfiles import StaticFiles
    if not os.path.exists("./static"):
        os.mkdir("./static")
    app.mount("/static", StaticFiles(directory="static"), name="static")


def register_router(app: FastAPI) -> None:
    """
    注册路由
    :param app:
    :return:
    """
    # 项目API
    app.include_router(
        api_v1_router,
    )


def register_cors(app: FastAPI) -> None:
    """
    支持跨域
    :param app:
    :return:
    """
    # if settings.DEBUG:
    if bool(os.getenv('DEBUG')) if os.getenv('DEBUG') else os.getenv('DEBUG'):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


def register_exception(app: FastAPI) -> None:
    """
    全局异常捕获
    注意 别手误多敲一个s
    exception_handler
    exception_handlers
    两者有区别
        如果只捕获一个异常 启动会报错
        @exception_handlers(UserNotFound)
    TypeError: 'dict' object is not callable
    :param app:
    :return:
    """

    # 自定义异常 捕获
    @app.exception_handler(custom_exc.TokenExpired)
    async def user_not_found_exception_handler(request: Request, exc: custom_exc.TokenExpired):
        """
        token过期
        :param request:
        :param exc:
        :return:
        """
        logger.error(
            f"token未知用户\nURL:{request.method}{request.url}\nHeaders:{request.headers}\n{traceback.format_exc()}")

        return resp.fail(message=exc.err_desc)

    @app.exception_handler(custom_exc.TokenAuthError)
    async def user_token_exception_handler(request: Request, exc: custom_exc.TokenAuthError):
        """
        用户token异常
        :param request:
        :param exc:
        :return:
        """
        logger.error(
            f"用户认证异常\nURL:{request.method}{request.url}\nHeaders:{request.headers}\n{traceback.format_exc()}")

        return resp.fail(resp.DataNotFound.set_msg(exc.err_desc))

    @app.exception_handler(custom_exc.AuthenticationError)
    async def user_not_found_exception_handler(request: Request, exc: custom_exc.AuthenticationError):
        """
        用户权限不足
        :param request:
        :param exc:
        :return:
        """
        logger.error(f"用户权限不足 \nURL:{request.method}{request.url}")
        return resp.fail(resp.PermissionDenied)

    @app.exception_handler(ValidationError)
    async def inner_validation_exception_handler(request: Request, exc: ValidationError):
        """
        内部参数验证异常
        :param request:
        :param exc:
        :return:
        """
        logger.error(
            f"内部参数验证错误\nURL:{request.method}{request.url}\nHeaders:{request.headers}\n{traceback.format_exc()}")
        return resp.fail(resp.BusinessError.set_msg(exc.errors()))

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        请求参数验证异常
        :param request:
        :param exc:
        :return:
        """
        logger.error(
            f"请求参数格式错误\nURL:{request.method}{request.url}\nHeaders:{request.headers}\n{traceback.format_exc()}")
        # return response_code.resp_4001(message='; '.join([f"{e['loc'][1]}: {e['msg']}" for e in exc.errors()]))
        return resp.fail(resp.InvalidParams.set_msg(exc.errors()))

    # 捕获全部异常
    @app.exception_handler(Exception)
    async def all_exception_handler(request: Request, exc: Exception):
        """
        全局所有异常
        :param request:
        :param exc:
        :return:
        """
        logger.error(
            f"全局异常\n{request.method}URL:{request.url}\nHeaders:{request.headers}\n{traceback.format_exc()}")
        return resp.fail(resp.ServerError)


ignoreUrl = ['/api/user/login', '/api/docs', '/api/openapi.json', '/api/test', '/api/user_action/add',
             '/api/test/send_message', '/api/test/consume_message']


def register_hook(app: FastAPI) -> None:
    """
    请求响应拦截 hook
    https://fastapi.tiangolo.com/tutorial/middleware/
    :param app:
    :return:
    """

    def de(func):
        async def wrapper():
            return func

        return wrapper

    async def set_body(request: Request):
        receive_ = await request._receive()

        async def receive():
            return receive_

        request._receive = receive

    # @app.middleware("http")
    # async def logger_request(request: Request, call_next) -> Response:
    #     # https://stackoverflow.com/questions/60098005/fastapi-starlette-get-client-real-ip
    #     # print('logger_request start')
    #     # print('request.client.host')
    #     data = 'todo'
    #     account = 'login'
    #     hs = request.headers
    #     token = hs.get("token")
    #     host = hs.get("host")
    #     req = dict(request)
    #     pageUrl = req['path']
    #     # ignoreUrl = ['/api/user/login', '/api/docs', '/api/openapi.json']
    #     print('pageUrl2')
    #     print(pageUrl)
    #     if pageUrl not in ignoreUrl and token is not None:
    #         payload = jwt.decode(
    #             token,
    #             # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    #             os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')]
    #         )
    #         account = payload.get("sub")
    #         # 解析token。将id从token中解析出来去。
    #         # try:
    #         #     payload = jwt.decode(
    #         #         token,
    #         #         # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    #         #         os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')]
    #         #     )
    #         #     account = payload.get("sub")
    #         #
    #         # except jwt.ExpiredSignatureError as e:
    #         #     # TODO token续期
    #         #     print('登录已经过期logger_request.')
    #         #     return resp.fail(resp.Unauthorized.set_msg('登录已经过期logger_request.'))
    #         # except Exception as e:
    #         #     return resp.fail(resp.Unauthorized.set_msg('登录失败，请重试logger_request。'), detail=str(e))
    #
    #     logger.info(
    #         f"访问记录:{request.method} url:{request.url} account:{account} IP:{host} data:{data}")
    #
    #     response = await call_next(request)
    #     # print(' logger_request end')
    #
    #     return response
    #     # try:
    #     #     response = await asyncio.wait_for(call_next(request), 20)
    #     #     return response
    #     # except asyncio.TimeoutError:
    #     #     print('Timeout error')
    #     #     if not db.is_closed():
    #     #         db.close()
    #     #     return resp.fail(resp.Timeout)

    # token拦截验证
    # 用户每次请求接口都需要验证是否在登录状态。（这里需要一个filter或则interceptor）获取token。
    # 解析token。将id从token中解析出来去。然后将用户的id作为key去redis中查询token。
# <<<<<<< Updated upstream
#     @app.middleware("http")
#     async def token_interceptor(request: Request, call_next):
#         # print('token_intercepter start')
#         # return resp.fail(resp.DataStoreFail.set_msg('账号已在其他设备登录.'))
#
#         req = dict(request)
#         # print('(req)')
#         # print((req))
#         pageUrl = req['path']
#         hs = request.headers
#         token = hs.get("token")
#         # print('token')
#         # print(token)
#         print('pageUrl1')
#         print(pageUrl)
#         # if pageUrl != '/api/user/login' and pageUrl != '/api/test':
#         if pageUrl not in ignoreUrl and token != None:
#
#             # 获取token。
#             hs = request.headers
#             token = hs.get("token")
#             # print(token, type(token))
#
#             # 解析token。将id从token中解析出来去。
#             try:
#                 payload = jwt.decode(
#                     token,
#                     # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
#                     os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')]
#                 )
#             except jwt.ExpiredSignatureError as e:
#                 # TODO token续期
#                 print('登录已经过期.token_interceptor')
#                 return resp.fail(resp.Unauthorized.set_msg('登录已经过期.'))
#                 # raise custom_exc.TokenExpired()
#             except Exception as e:
#                 return resp.fail(resp.Unauthorized.set_msg('登录失败，请重试。'), detail=str(e))
#             account = payload.get("sub")
#             # print(account)
#
#             # 然后将用户的id作为key去redis中查询token。
#             result = redis_client.get(account)
#             # print('redis_client result')
#             # print(result)
#             # 查询为空则表示登录过期/未登录。不为空则将解析出来的token和redis中的token作对比，如果相同，则用户状态正常则继续请求接口。如果不相同，则账号在其他设备登录.
#             if result != None and result != token:
#                 print('账号已在其他设备登录.token_interceptor')
#                 # return JSONResponse(
#                 #     status_code=401,
#                 #     content=jsonable_encoder({
#                 #         'status': 401,
#                 #         'msg': '账号已在其他设备登录.',
#                 #         "success": False,
#                 #         'detail':'账号已在其他设备登录.'
#                 #     })
#                 # )
#                 return resp.fail(resp.Unauthorized.set_msg('账号已在其他设备登录.'))
#                 # print('登录过期')
#                 # raise HTTPException(
#                 #     status_code=401, detail="账号已在其他设备登录")
#                 # return resp.fail(resp.DataStoreFail, detail='账号已在其他设备登录.')
#             else:
#                 response = await call_next(request)
#                 return response
#         elif pageUrl not in ignoreUrl and token == None:
#             return resp.fail(resp.Unauthorized.set_msg('登录已失效，请重新登录.'))
#         # print('token不为空 登录合法')
#
#         response = await call_next(request)
#         # print('token_intercepter end')
#
#         return response

# =======
    # @app.middleware("http")
    # async def token_interceptor(request: Request, call_next):
    #     # print('token_intercepter start')
    #     # return resp.fail(resp.DataStoreFail.set_msg('账号已在其他设备登录.'))
    #
    #     req = dict(request)
    #     # print('(req)')
    #     # print((req))
    #     pageUrl = req['path']
    #     hs = request.headers
    #     token = hs.get("token")
    #     # print('token')
    #     # print(token)
    #     # if pageUrl != '/api/user/login' and pageUrl != '/api/test':
    #     ignoreUrl = ['/api/user/login', '/api/docs', '/api/openapi.json', '/api/test', '/api/user_action/add']
    #     if pageUrl not in ignoreUrl and token != None:
    #
    #         # 获取token。
    #         hs = request.headers
    #         token = hs.get("token")
    #         # print(token, type(token))
    #
    #         # 解析token。将id从token中解析出来去。
    #         try:
    #             payload = jwt.decode(
    #                 token,
    #                 # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    #                 os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')]
    #             )
    #         except jwt.ExpiredSignatureError as e:
    #             # TODO token续期
    #             print('登录已经过期.token_interceptor')
    #             return resp.fail(resp.Unauthorized.set_msg('登录已经过期.'))
    #             # raise custom_exc.TokenExpired()
    #         except Exception as e:
    #             return resp.fail(resp.Unauthorized.set_msg('登录失败，请重试。'), detail=str(e))
    #         account = payload.get("sub")
    #         # print(account)
    #
    #         # 然后将用户的id作为key去redis中查询token。
    #         result = redis_client.get(account)
    #         print('redis_client result')
    #         print(result)
    #         # 查询为空则表示登录过期/未登录。不为空则将解析出来的token和redis中的token作对比，如果相同，则用户状态正常则继续请求接口。如果不相同，则账号在其他设备登录.
    #         if result != None and result != token:
    #             print('账号已在其他设备登录.token_interceptor')
    #             # return JSONResponse(
    #             #     status_code=401,
    #             #     content=jsonable_encoder({
    #             #         'status': 401,
    #             #         'msg': '账号已在其他设备登录.',
    #             #         "success": False,
    #             #         'detail':'账号已在其他设备登录.'
    #             #     })
    #             # )
    #             return resp.fail(resp.Unauthorized.set_msg('账号已在其他设备登录.'))
    #             # print('登录过期')
    #             # raise HTTPException(
    #             #     status_code=401, detail="账号已在其他设备登录")
    #             # return resp.fail(resp.DataStoreFail, detail='账号已在其他设备登录.')
    #         else:
    #             response = await call_next(request)
    #             return response
    #     elif pageUrl not in ignoreUrl and token == None:
    #         return resp.fail(resp.Unauthorized.set_msg('登录已失效，请重新登录.'))
    #
    #     response = await call_next(request)
    #     return response

    def de(func):
        async def wrapper():
            return func

        return wrapper

    async def set_body(request: Request):
        receive_ = await request._receive()

        async def receive():
            return receive_

        request._receive = receive

    # @app.middleware("http")
    # async def logger_request(request: Request, call_next) -> Response:
    #     # https://stackoverflow.com/questions/60098005/fastapi-starlette-get-client-real-ip
    #     # print('logger_request start')
    #     # print('request.client.host')
    #     data = 'todo'
    #     account = 'login'
    #     hs = request.headers
    #     token = hs.get("token")
    #     host = hs.get("host")
    #     if token != None:
    #         # 解析token。将id从token中解析出来去。
    #         try:
    #             payload = jwt.decode(
    #                 token,
    #                 # settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    #                 os.getenv('SECRET_KEY'), algorithms=[os.getenv('ALGORITHM')]
    #             )
    #             account = payload.get("sub")
    #
    #         except jwt.ExpiredSignatureError as e:
    #             # TODO token续期
    #             print('登录已经过期logger_request.')
    #             return resp.fail(resp.Unauthorized.set_msg('登录已经过期logger_request.'))
    #         except Exception as e:
    #             return resp.fail(resp.Unauthorized.set_msg('登录失败，请重试logger_request。'), detail=str(e))
    #
    #     logger.info(
    #         f"访问记录:{request.method} url:{request.url} account:{account} IP:{host} data:{data}")
    #
    #     # response = await call_next(request)
    #     # return response
    #     try:
    #         response = await asyncio.wait_for(call_next(request), 10)
    #         return response
    #     except asyncio.TimeoutError:
    #         print('Timeout error')
    #         if not db.is_closed():
    #             db.close()
    #         return resp.fail(resp.Timeout)

# >>>>>>> Stashed changes

def register_init(app: FastAPI) -> None:
    """
    初始化连接
    :param app:
    :return:
    """

    @app.on_event("startup")
    async def init_connect():
        # print("startup init_connect")
        # # 连接redis
        redis_client.init_redis_connect()


        ### kafka数据库链接
        # kafka_client.init_kafka_producer()
        # # kafka_client.init_kafka_consumer(['flinksql'])
        # kafka_client.init_kafka_consumer([os.getenv('KAFKA_TOPIC')])




        # # 初始化 apscheduler
        # schedule.init_scheduler()
        # conn_params = {'connect_timeout': 5}  # 设置连接超时为 5 秒
        # db.init(database=os.getenv('MYSQL_DATABASE'),
        #         host=os.getenv('MYSQL_HOST'),
        #         port=int(os.getenv('MYSQL_PORT')) if os.getenv('MYSQL_PORT') else os.getenv('MYSQL_PORT'),
        #         user=os.getenv('MYSQL_USERNAME'),
        #         password=os.getenv('MYSQL_PASSWORD'),
        #     **conn_params)
        db.connect()

        # db.execute_sql("set global time_zone='+08:00'")
        # 使用 cursor() 方法创建一个游标对象
        # cursor = db.cursor()
        # cursor.execute("flush privileges")

    @app.on_event('shutdown')
    async def shutdown_connect():
        """
        关闭
        :return:
        """
        # schedule.shutdown()
        # 在应用关闭时，关闭生产者和消费者
        kafka_client.shutdown()
        print("shutdown shutdown_connect")

        if not db.is_closed():
            db.close()
