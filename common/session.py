#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/10/16 11:42
# @Author  : CoderCharm
# @File    : session.py
# @Software: PyCharm
# @Github  : github/CoderCharm
# @Email   : wg_python@163.com
# @Desc    :
"""

"""
import asyncio
import math
import datetime
import os

import aiomysql
import peewee_async
import pytz
from peewee import _ConnectionState, Model, ModelSelect, SQL, DateTimeField, MySQLDatabase, PostgresqlDatabase
from contextvars import ContextVar

# 异步数据库
from peewee_async import Manager, MySQLDatabase as AsyncMySQLDatabase
from playhouse.shortcuts import ReconnectMixin
# 异步数据库
# 连接池
from peewee_async import PooledMySQLDatabase as AsyncPooledMySQLDatabase
from core.config import settings
from fastapi import Depends

db_state_default = {"closed": None, "conn": None,
                    "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())


async def reset_db_state():
    # print(("reset_db_state()"))
    db._state._state.set(db_state_default.copy())
    db._state.reset()


def get_db(db_state=Depends(reset_db_state)):
    pass
    try:
        # print('session.db.connect()')
        db.connect()
        yield
    finally:
        if not db.is_closed():
            # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!! db.close()')
            db.close()


class PeeweeConnectionState(_ConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]


# -----------------------------------------------------------------------------------

# 同步数据库
# 同步数据库断线重连类
class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


# -----------------------------------------------------------------------------------


# db = AsyncMySQLDatabase(**db_config)
# 异步+断线重连
class ReconnectAsyncMySQLDatabase(ReconnectMixin, AsyncMySQLDatabase):
    pass


db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'port': int(os.getenv('MYSQL_PORT')) if os.getenv('MYSQL_PORT') else os.getenv('MYSQL_PORT'),
    'user': os.getenv('MYSQL_USERNAME'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    # 'stale_timeout' : 60,
}
# 超时后将回收连接。max_connections=8,
# 打开的连接数的上限。stale_timeout=300,
db = ReconnectAsyncMySQLDatabase(**db_config)

# -----------------------------------------------------------------------------------
# 创建 aiomysql 连接池

# peewee 同步、异步、断线重连、连接池 https://www.cnblogs.com/gcxblogs/p/14969019.html
# 断线重连+连接池
class ReconnectAsyncPooledMySQLDatabase(ReconnectMixin, AsyncPooledMySQLDatabase):
    _instance = None

    @classmethod
    def get_db_instance(cls):
        db_config = {
            'host': os.getenv('MYSQL_HOST'),
            'port': int(os.getenv('MYSQL_PORT')) if os.getenv('MYSQL_PORT') else os.getenv('MYSQL_PORT'),
            'user': os.getenv('MYSQL_USERNAME'),
            'password': os.getenv('MYSQL_PASSWORD'),
            'database': os.getenv('MYSQL_DATABASE'),
            # 'stale_timeout' : 60,
            # 'connect_timeout' : 10
        }
        if not cls._instance:
            cls._instance = cls(**db_config, max_connections=500)
        return cls._instance


# db = ReconnectAsyncPooledMySQLDatabase.get_db_instance()
# -----------------------------------------------------------------------------------

# 然后我们需要将db传入到Manager中得到一个async_db
# loop = asyncio.new_event_loop()  # Note: custom loop!,loop=loop
# # 丢到循环里面
async_db = Manager(db)
async_db._state = PeeweeConnectionState()
db._state = PeeweeConnectionState()


# # No need for sync anymore!
# db.set_allow_sync(False)
#
# # 从现在开始，我们可能只需要异步调用，并将同步视为不需要或错误：
# async_db.database.allow_sync = False


class BaseModel(Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        """将事务改成atomic_async"""
        self.trans = db.atomic_async
        """添加一个Manager类"""
        self.object = Manager(db)

    # deleted_at = DateTimeField()
    createAt = DateTimeField(column_name='create_at')
    updateAt = DateTimeField(column_name='update_at')

    # @classmethod
    # def undelete(cls):
    #     # for logic delete
    #     return cls.select().where(SQL("deleted_at is NULL"))

    class Meta:
        database = db


def paginator(query: ModelSelect, page: int, page_size: int, order_by: str = "id ASC"):
    count = query.count()
    if page < 1:
        page = 1

    if page_size <= 0:
        page_size = 10

    if page_size >= 100:
        page_size = 100

    if page == 1:
        offset = 0
    else:
        offset = (page - 1) * page_size

    query = query.offset(offset).limit(page_size).order_by(SQL(order_by))

    total_pages = math.ceil(count / page_size)

    paginate = {
        "total_pages": total_pages,
        "count": count,
        "current_page": page,
        "pre_page": page - 1 if page > 1 else page,
        "next_page": page if page == total_pages else page + 1
    }

    return list(query.dicts()), paginate

# db = ReconnectAsyncMySQLDatabase(
#     os.getenv('MYSQL_DATABASE'),
#     host=os.getenv('MYSQL_HOST'),
#     # port=int(os.getenv('MYSQL_PORT')),
#     port=int(os.getenv('MYSQL_PORT')) if os.getenv('MYSQL_PORT') else os.getenv('MYSQL_PORT'),
#     user=os.getenv('MYSQL_USERNAME'),
#     password=os.getenv('MYSQL_PASSWORD'),
#
#     # host=settings.MYSQL_HOST,
#     # port=settings.MYSQL_PORT,
#     # user=settings.MYSQL_USERNAME,
#     # password=settings.MYSQL_PASSWORD,
#     charset='utf8',
#
#     # 如果用户账号使用sha256_password认证，传输过程中必须保护密码；TLS 是首选机制，但如果它不可用，则将使用 RSA 公钥加密。
#     # 要指定服务器的 RSA 公钥，请使用ServerRSAPublicKeyFile连接字符串设置，或设置AllowPublicKeyRetrieval=True为允许客户端自动从服务器请求公钥。
#     # 请注意，这AllowPublicKeyRetrieval=True 可能允许恶意代理执行 MITM 攻击以获取明文密码，因此False默认情况下必须显式启用它。
#
#     # param ssl_disabled：禁用 TLS 使用的布尔值
#     # ssl_disabled=True,
#
#     # param auth_plugin_map：处理该插件的类的插件名称字典。
#     #     该类将 Connection 对象作为构造函数的参数。
#     #     该类需要一个身份验证方法，该方法将身份验证数据包作为
#     #     一个论点。 对于对话框插件，可以使用提示（echo，prompt）方法
#     #     （如果没有身份验证方法）从用户返回字符串。（实验性）
#
#     # "caching_sha2_password"
#     # "sha256_password"
#     # "mysql_native_password"
#     # "client_ed25519"
#     # "mysql_old_password"
#     # "mysql_clear_password"
#     # auth_plugin_map='mysql_native_password',
#     #  :p aram server_public_key：SHA256 身份验证插件公钥值。（默认值：None）
#     # server_public_key='SHA256',
#
#     # read_default_file=os.getenv('BASE_PATH')+"\my.ini"
#     # ssl=,
#     # max_connections=300,
#     # stale_timeout=60,
#     # pool_recycle=60,
# )
