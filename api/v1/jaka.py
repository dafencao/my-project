import asyncio
import subprocess
from typing import Any, List, Optional
from datetime import datetime, timedelta

import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, Header
from sqlalchemy.sql.coercions import cls

from jaka.jaka_function import  JakaFunction
from schemas.response import resp

router = APIRouter()
# 坐标系
COORD_BASE = 0
COORD_JOINT = 1
COORD_TOOL = 2

# 运动模式
ABS = 0 # 绝对运动
INCR = 1 # 增量运动

#笛卡尔空间

cart_x = 0 #x 方向
cart_y = 1 #y 方向
cart_z = 2 #z 方向
cart_rx = 3 #rx 方向
cart_ry = 4 #ry 方向
cart_rz = 5 #rz 方向

@router.get("/jaka", summary="jaka", name="jaka")
async def run_jaka(param):
    inform = param

    if inform == 'power':
        result = await cls.power_on()
        return resp.ok(data=result)

    if inform == 'enable':
        result = await cls.enable_robot()
        return resp.ok(data=result)

    if inform == 'jogStart':
        result = await cls.jog_start()
        return resp.ok(data=result)

    if inform == 'jogCar':
        result = await cls.jog_Car()
        return resp.ok(data=result)

    if inform == 'circularMove':
        result = await cls.circular_move_extend()
        return resp.ok(data=result)