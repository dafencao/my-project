
from datetime import datetime, date
import re
from typing import List, Optional, Union

import pytz
from peewee import Model
from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field, constr, validator

from utils.tools_func import tz
class UserTestBase(BaseModel):
    id: Optional[int]
    password: Optional[str]
    realName: Optional[str]
    account: Optional[str]
    email: Optional[EmailStr] = ''


    phone: Optional[constr(min_length=11, max_length=11)]

    oraCode: Optional[int] = None
    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None

class UserTestUpdate(BaseModel):
    id: int
    postid: int

    password: Optional[str]
    realName: Optional[str]
    account: Optional[str]
    email: Optional[EmailStr] = ''

    phone: Optional[constr(min_length=11, max_length=11)]

    oraCode: Optional[int] = None
    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None

class TestPostAdd(BaseModel):
    id: int
    post: Optional[str]


    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None