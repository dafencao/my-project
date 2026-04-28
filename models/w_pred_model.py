from common.session import BaseModel, paginator, db, async_db
from peewee import AutoField, CharField, DecimalField, TextField, IntegerField, BooleanField, DateTimeField
from playhouse.shortcuts import model_to_dict, dict_to_model
from sqlalchemy.orm import relationship
from playhouse.mysql_ext import JSONField

from models.usermenu import Usermenu
from schemas.request import sys_user_schema

from peewee import fn, JOIN
import datetime

from utils.tools_func import convert_arr, convert_num_arr

class TrainedModel(BaseModel):
    id = AutoField(primary_key=True)
    model_name = CharField(max_length=100)
    version = CharField(max_length=50)
    model_path = CharField(max_length=255)
    
    material_id = IntegerField()
    joint_id = IntegerField()
    method_id = IntegerField()
    
    # 【核心修改】最大变形量相对误差 (例如 5.25 表示 5.25%)
    max_def_rel_error = DecimalField(max_digits=10, decimal_places=4, null=True) 
    
    description = TextField(null=True) 
    trained_on_batch = CharField(max_length=50, null=True)
    metrics = JSONField(null=True)
    is_deployed = BooleanField(default=False) 
    
    created_at = DateTimeField(null=True)
    updated_at = DateTimeField(null=True)

    class Meta:
        table_name = 'wtrained_models'