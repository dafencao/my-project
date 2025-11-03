from datetime import datetime, date
import re
from typing import List, Optional, Union

import pytz
from peewee import Model
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field, constr, validator

from utils.tools_func import tz


# 机车
class IntroBase(BaseModel):

    # id: Optional[str]
    order: Optional[int]
    trainType: Optional[int]
    imagePosition: Optional[List[int]]
    circle: Optional[List[int]]
    linePoints: Optional[List[int]]
    text: Optional[List[int]]
    circleNode: Optional[List[int]]
    # radius: Optional[int] = 90
    show: Optional[int]



    # createAt: Optional[datetime] = None
    # updateAt: Optional[datetime] = None


class IntroUpdate(BaseModel):

    id: Optional[str]
    order: Optional[int]
    trainType: Optional[int]
    imagePosition: Optional[List[float]]
    circle: Optional[List[float]]
    linePoints: Optional[List[float]]
    text: Optional[List[float]]
    circleNode: Optional[List[float]]
    radius: Optional[int]
    show: Optional[int]

    # createAt: Optional[datetime] = None
    # updateAt: Optional[datetime] = None


class KafkaSend(BaseModel):

    message: Optional[str]



# 动车

# class BulletBase(BaseModel):
#
#     # id: Optional[int]
#     sn: Optional[int]
#     trainType: Optional[str]
#     imagePosition: Optional[List[float]]
#     circle: Optional[List[float]]
#     linePoint: Optional[List[float]]
#     text: Optional[List[float]]
#     circleNode: Optional[List[float]]
#     radius: Optional[int]
#
#     createAt: Optional[datetime] = None
#     updateAt: Optional[datetime] = None
#
#
# class BulletUpdate(BaseModel):
#
#     id: Optional[int]
#     sn: Optional[int]
#     trainType: Optional[str]
#     imagePosition: Optional[List[float]]
#     circle: Optional[List[float]]
#     linePoint: Optional[List[float]]
#     text: Optional[List[float]]
#     circleNode: Optional[List[float]]
#     radius: Optional[int]
#
#     createAt: Optional[datetime] = None
#     updateAt: Optional[datetime] = None