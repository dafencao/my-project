import pytz

from utils.tools_func import tz

'''
Descripttion: 
version: 
Author: congsir
Date: 2023-04-04 15:08:09
LastEditors: Please set LastEditors
LastEditTime: 2023-04-19 14:48:02
'''

from models.userrole import Permission, RoleMenuRelp, RolePermRelp, Userrole
from common import deps, logger
from common.session import db, async_db
from core import security
from fastapi import APIRouter, Depends, HTTPException, Form, status
from datetime import datetime, timedelta
from typing import Any,List
from schemas.response import resp
from schemas.request import sys_userrole_schema
from models.user import UserRoleRelp, Userinfo
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError

router = APIRouter()

