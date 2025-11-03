
from typing import Any
from datetime import timedelta, datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException, Form
from common.session import get_db

from core import security
from models.department import Department
from common import deps, logger
from schemas.response import resp
from schemas.request import sys_department_schema
from playhouse.shortcuts import model_to_dict, dict_to_model
from peewee import fn, IntegrityError

router = APIRouter()


@router.post("/sys/department/add", summary="添加部门", name="添加部门", dependencies=[Depends(get_db)])
async def add_department(
    department: sys_department_schema.DepartmentBase
) -> Any:
    department.create_time=datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')

    try:
        department = dict(department)
        result =await Department.add_department(department)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('部门编码已存在！'))

    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))

    return resp.ok(data=result)


@router.delete("/sys/department/delete", summary="删除部门", name="删除部门", dependencies=[Depends(get_db)])
async def del_department(
    id : int
) -> Any:
    try:
        result = await Department.del_by_department_id(id)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)

@router.put("/sys/department/edit/{dept_id}", summary="编辑菜单", name="编辑菜单")
async def edit_department(
    department: sys_department_schema.DepartmentUpdate,
) -> Any:
    department.updateAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    # print(department)
    department = dict(department)

    try:    
        result =await Department.update_department(department)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('部门编码已存在！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
    return resp.ok(data=result)

@router.post("/sys/department/show", summary="根据条件筛选部门", name="查询部门列表")
async def show_department(querydepartment: sys_department_schema.DepartmentQuery
) -> Any:
    querydepartment = dict(querydepartment)
    try:
        result =await Department.fuzzy_query(querydepartment)
        print(result)
        return resp.ok(data=result)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    pass
