from datetime import datetime
from typing import Any

import pytz
from fastapi import APIRouter, Depends
from peewee import IntegrityError

from common.session import get_db, async_db

from models.fan import FanApplicationModel, FanCategory, Fan
from schemas.request import sys_fan_schema
from schemas.response import resp

router = APIRouter()


@router.get("/group", summary="获取风机类型树", name="", dependencies=[Depends(get_db)])
async def get_fan_category() -> Any:
    result = await FanCategory.select_group_all()
    return resp.ok(data=result)

    categoryDict = {}

    # result = list(result)
    temp = []
    for item in result:
        if item['parentId']==0:
            categoryDict[item['id']] = item['name']
            continue
        temp.append(item)
    result = temp

    res = {}
    for item in result:
        if item['parentId']!=0:
            item['series']=categoryDict[item['parentId']]
        if item['series'] not in res.keys():
            res[item['series']] = []
        if item['name'] not in res[item['series']]:
            res[item['series']].append(item['name'])
    return resp.ok(data=res)


@router.get("/all", summary="获取所有风机类型", dependencies=[Depends(get_db)], name="")
async def get_fan_category() -> Any:
    db = await FanCategory.select_group_all()
    db = list(db)

    result = []
    for item in db:
        if item['parentId']!=0:
            result.append(item['name'])
    if result:
        return resp.ok(data=result)


@router.post("/add", summary="添加风机类型", name="添加风机类型", dependencies=[Depends(get_db)])
async def add_category(
        req: sys_fan_schema.CategoryBase
) -> Any:
    req.createAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    req.updateAt =  req.createAt
    try:
        category = dict(req)
        result = await FanCategory.add(category)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('风机分类编码已存在！'))
    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok(data=result)


@router.delete("/delete", summary="删除风机类型", name="删除风机类型", dependencies=[Depends(get_db)])
async def del_category(
        id: int
) -> Any:
    try:
        async_db.execute(Fan.select().where(Fan.seriesId==id).dicts())
        result = await FanCategory.del_by_category_id(id)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok(data=result)


@router.put("/edit", summary="编辑风机类型", name="编辑风机类型")
async def edit_category(
        req: sys_fan_schema.CategoryUpdate,
) -> Any:
    req.updateAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    # print(department)
    category = dict(req)

    try:
        result = await FanCategory.update_category(category)
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('风机分类编码已存在！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
    return resp.ok(data=result)


@router.post("/show", summary="根据条件筛选风机类型", name="查询风机类型列表")
async def show_category(req: sys_fan_schema.CategoryQuery
                        ) -> Any:
    req = dict(req)
    try:
        result = await FanCategory.fuzzy_query(req)
        print(result)
        return resp.ok(data=result)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    pass
