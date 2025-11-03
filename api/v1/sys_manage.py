from datetime import datetime
from typing import List
from typing import Any, List, Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException, Form, Header
from peewee import IntegrityError

from common.session import get_db, db, async_db
from models.fan import FanApplicationModel, FanCoolObject, FanCategory
from models.fan_introduction import Fan_introduction
from models.user import Level, Userpost, Userline, Department
from schemas.request import sys_manage
from schemas.response import resp

router = APIRouter()


@router.post("/group/show", summary="根据条件筛选组", name="查询组列表")
async def show_group_info(req: sys_manage.GroupQuery) -> Any:
    if (not req.groupId) or len(req.groupId) == 0:
        req.groupId = ['level', 'line', 'post', '应用车型','冷却对象' ]
    result = []
    try:
        result1=[]
        if 'level' in req.groupId:
            db =await async_db.execute(   Level.select(Level.id, Level.updateAt, Level.code.alias('key'), Level.name.alias('value'), ).where(
                Level.code.contains(req.key), Level.name.contains(req.value)).dicts())

            result1 = list(db)
            for r in result1:
                r['groupId'] = 'level'
        result2=[]
        if 'post' in req.groupId:
            db =await async_db.execute(   Userpost.select(Userpost.id, Userpost.updateAt, Userpost.code.alias('key'),
                                 Userpost.name.alias('value')).where(
                Userpost.code.contains(req.key), Userpost.name.contains(req.value)).dicts())
            result2 = list(db)
            for r in result2:
                r['groupId'] = 'post'
        result3=[]
        if 'line' in req.groupId:
            db =await async_db.execute(   Userline.select(Userline.id, Userline.updateAt, Userline.code.alias('key'),
                                 Userline.name.alias('value')).where(
                Userline.code.contains(req.key), Userline.name.contains(req.value)).dicts())
            result3 = list(db)
            for r in result3:
                r['groupId'] = 'line'

        result4 = []
        if 'department' in req.groupId:
            db = await async_db.execute(  Department.select(Department.id, Department.updateAt, Department.code.alias('key'),
                                 Department.name.alias('value')).where(
                Department.code.contains(req.key), Department.name.contains(req.value)).dicts())
            result4 = list(db)
            for r in result4:
                r['groupId'] = 'department'

        result5 = []
        if '应用车型' in req.groupId:
            db =await async_db.execute( FanApplicationModel.select(FanApplicationModel.id, FanApplicationModel.updateAt,
                                            FanApplicationModel.code.alias('key'),
                                            FanApplicationModel.name.alias('value')).where(
                FanApplicationModel.code.contains(req.key), FanApplicationModel.name.contains(req.value)).dicts())
            result5 = list(db)
            for r in result5:
                r['groupId'] = '应用车型'
        result6 = []
        if '冷却对象' in req.groupId:
            db =await async_db.execute(  FanCoolObject.select(FanCoolObject.id, FanCoolObject.updateAt,
                                            FanCoolObject.code.alias('key'),
                                            FanCoolObject.name.alias('value')).where(
                FanCoolObject.code.contains(req.key), FanCoolObject.name.contains(req.value)).dicts())
            result6 = list(db)
            for r in result6:
                r['groupId'] = '冷却对象'
        result7 = []
        if '风机类型' in req.groupId:
            db =await async_db.execute(   FanCategory.select(FanCategory.id, FanCategory.updateAt,
                                      FanCategory.series.alias('key'),
                                      FanCategory.name.alias('value')).where(
                FanCategory.series.contains(req.key), FanCategory.name.contains(req.value)).dicts())
            result7 = list(db)
            for r in result7:
                r['groupId'] = '风机类型'
        result.extend(result1)
        result.extend(result2)
        result.extend(result3)
        result.extend(result4)
        result.extend(result5)
        result.extend(result6)
        result.extend(result7)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound)
    result = sorted(result, key=lambda e: e.__getitem__(
        'updateAt'), reverse=True)

    total = len(result)
    print(total)
    result = result[(req.current - 1) *
                    req.pageSize:req.current * req.pageSize]
    return resp.ok(data=result, total=total)


@router.post("/group/add", summary="新增组", name="添加组")
async def add_group(
        req: sys_manage.GroupCreate
) -> Any:
    req.createAt=datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')),'%Y-%m-%d %H:%M:%S')
    req.updateAt = req.createAt
    try:
        async with db.atomic_async():
            if 'level' == req.groupId:
                # Level.create(code=req.key, name=req.value, createAt=req.createAt, updateAt=req.createAt)
                await async_db.create(Level,**{'code':req.key, 'name':req.value, 'createAt':req.createAt, 'updateAt':req.createAt})

            if 'post' == req.groupId:
                # Userpost.create(code=req.key, name=req.value, createAt=req.createAt, updateAt=req.createAt)
                await async_db.create(Userpost,**{'code':req.key, 'name':req.value, 'createAt':req.createAt, 'updateAt':req.createAt})

            if 'line' == req.groupId:
                # Userline.create(code=req.key, name=req.value, createAt=req.createAt, updateAt=req.createAt)
                await async_db.create(Userline,**{'code':req.key, 'name':req.value, 'createAt':req.createAt, 'updateAt':req.createAt})

            if 'department' == req.groupId:
                # Department.create(code=req.key, name=req.value, createAt=req.createAt, updateAt=req.createAt)
                await async_db.create(Department,**{'code':req.key, 'name':req.value, 'createAt':req.createAt, 'updateAt':req.createAt})

            if '应用车型' == req.groupId:
                await async_db.create(FanApplicationModel,**{'code':req.key, 'name':req.value, 'createAt':req.createAt, 'updateAt':req.createAt})
                # FanApplicationModel.create(code=req.key, name=req.value, createAt=req.createAt, updateAt=req.createAt)
            if '冷却对象' == req.groupId:
                await async_db.create(FanCoolObject,**{'code':req.key, 'name':req.value, 'createAt':req.createAt, 'updateAt':req.createAt})
                # FanCoolObject.create(code=req.key, name=req.value, createAt=req.createAt, updateAt=req.createAt)

            if '风机类型' == req.groupId:
                res = list(
                    await async_db.execute(  FanCategory.select().where(FanCategory.series == req.key, FanCategory.name == req.value, ).dicts()))
                if len(res)!=0:
                    return resp.fail(resp.DataStoreFail.set_msg('key已存在！'))
                # FanCategory.create(series=req.key, name=req.value, createAt=req.createAt, updateAt=req.createAt)
                await async_db.create(FanCategory,**{'series':req.key, 'name':req.value, 'createAt':req.createAt, 'updateAt':req.createAt})

    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('key已存在！'))
    except Exception as e:
        # print(e)
        # print(type(e))
        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok()


@router.delete("/group/delete", summary="删除组", name="删除组")
async def del_userinfo_group(
        req: sys_manage.GroupDelete
) -> Any:
    try:
    # if True:
        if req.groupId == 'level':
            await async_db.execute(Level.delete().where(Level.id == req.id) )
        elif req.groupId == 'line':
            await async_db.execute(Userline.delete().where(Userline.id == req.id) )
        elif req.groupId == 'post':
            await async_db.execute(Userpost.delete().where(Userpost.id == req.id) )
        elif req.groupId == 'department':
            await async_db.execute(Department.delete().where(Department.id == req.id) )
        elif req.groupId == '应用车型':
            await async_db.execute(FanApplicationModel.delete().where(FanApplicationModel.id == req.id))
        elif req.groupId == '冷却对象':
            # 数据完整性判断
            coolObjectRecord = await async_db.execute(FanCoolObject.select().where(FanCoolObject.id == req.id).dicts())
            coolObjectRecord = list(coolObjectRecord)
            code = coolObjectRecord[0]['code']
            # Fan_introduction
            record = await async_db.execute(Fan_introduction.select().where(Fan_introduction.coolObject == code).dicts())
            record = list(record)
            if len(record) > 0:
                return resp.fail(resp.DataDestroyFail.set_msg('删除失败，请检查风机产品信息。'))
            await async_db.execute(FanCoolObject.delete().where(FanCoolObject.id == req.id))
        elif req.groupId == '风机类型':
            await async_db.execute(FanCategory.delete().where(FanCategory.id == req.id) )
        else:
            print("暂无分组")
            return resp.fail(resp.DataDestroyFail.set_msg('暂无分组'))

    except Exception as e:
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    return resp.ok()


@router.put("/group/update", summary="修改组", name="修改组")
async def edit_userinfo_group(
        req: sys_manage.GroupCompareUpdate
) -> Any:
    lastData = req.last
    newData = req.new
    lastData.updateAt=datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')),'%Y-%m-%d %H:%M:%S')
    newData.updateAt = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')),'%Y-%m-%d %H:%M:%S')
    try:
    # if True:
        async with db.atomic_async():
            if lastData.groupId == 'level':
                await async_db.execute(Level.delete().where(Level.id == lastData.id) )
            elif lastData.groupId == 'line':
                await async_db.execute(Userline.delete().where(Userline.id == lastData.id) )
            elif lastData.groupId == 'post':
                await async_db.execute(Userpost.delete().where(Userpost.id == lastData.id) )
            elif lastData.groupId == 'department':
                await async_db.execute(Department.delete().where(Department.id == lastData.id) )
            elif lastData.groupId == '应用车型':
                await async_db.execute(FanApplicationModel.delete().where(FanApplicationModel.id == lastData.id) )
            elif lastData.groupId == '冷却对象':
                await async_db.execute(FanCoolObject.delete().where(FanCoolObject.id == lastData.id) )
            elif lastData.groupId == '风机类型':
                await async_db.execute(FanCategory.delete().where(FanCategory.id == lastData.id) )
            else:
                print("暂无分组")
                return resp.fail(resp.DataDestroyFail.set_msg('暂无分组'))
            if 'level' == newData.groupId:
                # Level.create(code=newData.key, name=newData.value,   updateAt=newData.updateAt)
                await async_db.create(Level,**{'code':newData.key, 'name':newData.value,   'updateAt':newData.updateAt})

            if 'post' == newData.groupId:
                # Userpost.create(code=newData.key, name=newData.value, updateAt=newData.updateAt)
                await async_db.create(Userpost,**{'code':newData.key, 'name':newData.value,   'updateAt':newData.updateAt})

            if 'line' == newData.groupId:
                # Userline.create(code=newData.key, name=newData.value, updateAt=newData.updateAt)
                await async_db.create(Userline,**{'code':newData.key, 'name':newData.value,   'updateAt':newData.updateAt})

            if 'department' == newData.groupId:
                # Department.create(code=newData.key, name=newData.value, updateAt=newData.updateAt)
                await async_db.create(Department,**{'code':newData.key, 'name':newData.value,   'updateAt':newData.updateAt})

            if '应用车型' == newData.groupId:
                # FanApplicationModel.create(code=newData.key, name=newData.value, updateAt=newData.updateAt)
                await async_db.create(FanApplicationModel,**{'code':newData.key, 'name':newData.value,   'updateAt':newData.updateAt})

            if '冷却对象' == newData.groupId:
                # FanCoolObject.create(code=newData.key, name=newData.value, updateAt=newData.updateAt)
                await async_db.create(FanCoolObject,**{'code':newData.key, 'name':newData.value, 'updateAt':newData.updateAt})

            if '风机类型' == newData.groupId:
                # FanCategory.create(series=newData.key, name=newData.value, updateAt=newData.updateAt)
                await async_db.create(FanCategory,**{'series':newData.key, 'name':newData.value, 'updateAt':newData.updateAt})

        return resp.ok( )
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('key已存在！'))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))
