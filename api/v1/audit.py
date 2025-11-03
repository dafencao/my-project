import os
import uuid
from datetime import datetime
from typing import Any

import pytz
from fastapi import Depends, APIRouter
from peewee import IntegrityError
from playhouse.shortcuts import dict_to_model, model_to_dict

from api.v1.fan import get_perf_line_equation, range_exclusion, get_save_bizeId
from common import deps
from common.session import get_db, async_db, db
from models.audit import AuditRecord
from models.fan import Fan
from models.fan_perf_data import PerfData
from models.file_info import FileInfo
from models.update_fan_record import FanUpdateRecord, FanUpdateRecordRelp
from models.user import Userinfo
from schemas.response import resp
from schemas.request import sys_fan_schema
from utils.file import fileNameDict, get_file_name, get_url, img_str_to_url_list

router = APIRouter()


@router.post("/fan/getPassedFanVersionData", summary="查询风机型号历史版本", name="", dependencies=[Depends(get_db)])
async def get_passed_fan_version_data(
        item_dict: dict
) -> Any:
    id = item_dict['id']

    try:
        fan = await FanUpdateRecord.single_by_id(id)
        if fan['status'] != 'pass':
            return resp.ok(data=[])
        result = await async_db.execute(FanUpdateRecord.select().where(
            FanUpdateRecord.status == 'passed',
            # FanUpdateRecord.status.not_in(['pass','audit','auditAlter','draft']),
            FanUpdateRecord.model == item_dict['model'],
            FanUpdateRecord.figNum == item_dict['figNum'],
            FanUpdateRecord.version == item_dict['version'],
        ).order_by(FanUpdateRecord.createAt.desc()).dicts())
        result = list(result)
    except Exception as e:
        return resp.fail(resp.DataNotFound, detail=str(e))
    return resp.ok(data=result)


@router.post("/fan/auditShow", summary="任意字段筛选风机型号", name="", dependencies=[Depends(get_db)])
async def audit_show_fans(
        # item_dict:dict
        req: sys_fan_schema.FanQuery,
        userInfo: Userinfo = Depends(deps.get_current_userinfo),
        userPerms: Userinfo = Depends(deps.get_current_user_perm)
) -> Any:
    # print('userInfo')
    # print(userInfo)
    # /fan/1:auth_show_all
    item_dict = dict(req)

    item_dict['createBy'] = None
    # 根据其他条件初次筛选
    item_dict['currentUser'] = None
    if '/fan/5' not in userPerms:  # and not req.manage
        item_dict['createBy'] = userInfo['account']
        # item_dict['status'] = []

    if req.manage:
        # 检查manage权限

        if '/fan/5:audit' not in userPerms and '/fan/5:auditByLead' not in userPerms and '/fan/5:auditAlter' not in userPerms:
            return resp.fail(resp.Unauthorized.set_msg('当前用户无审核管理权限！'))
        status = []

        if '/fan/5:audit' in userPerms:
            status.append('audit')
        if '/fan/5:auditAlter' in userPerms:
            status.append('auditAlter')
        if '/fan/5:auditByLead' in userPerms:
            status.append('auditByLead')
        if item_dict['status']:
            if item_dict['status'] in status:
                item_dict['status'] = [item_dict['status']]
            else:
                return resp.fail(resp.Unauthorized.set_msg('操作无权限！'))
        else:
            item_dict['status'] = status
        # if '/fan/5:audit' in userPerms and '/fan/5:auditByLead' not in userPerms:
        #     item_dict['status'] = ['audit','auditAlter']
        # if '/fan/5:audit' not in userPerms and '/fan/5:auditByLead' in userPerms:
        #     item_dict['status'] = ['auditByLead']
        # if '/fan/5:audit' in userPerms and '/fan/5:auditByLead' in userPerms:
        #     item_dict['status'] = ['audit','auditAlter','auditByLead']
        item_dict['createBy'] = None
        item_dict['currentUser'] = userInfo['account']
        item_dict['excludeStatus'] = None
    elif not req.manage:
        # item_dict['status'] = ['auditByLead']
        item_dict['createBy'] = userInfo['account']
        item_dict['excludeStatus'] = ['passed']
        # item_dict['excludeStatus'] = ['passed', 'rejectedAlter', 'rejected']
        if item_dict['status']:
            item_dict['status'] = [item_dict['status']]
    print('item_dict')
    print(item_dict)
    isShow = False
    for key in item_dict:
        if key in ['flowRate', 'fullPressure', 'motorSpeed', 'shaftPower',
                   'applicationModelId', 'applicationModel', 'model', 'coolObject', 'category', 'figNum', 'sortRange']:
            if item_dict[key]:
                isShow = True
                break

    if '/fan/1:auth_show_all' not in userPerms and (not isShow):
        return resp.ok(data=[], total=0)
    # try:
    result = await FanUpdateRecord.fuzzy_query_by_dict(item_dict, False)
    # except Exception as e:
    #     # print(e)
    #     return resp.fail(resp.DataNotFound, detail=str(e))

    total = len(result)
    # 分页
    current = int(req.current)
    pageSize = int(req.pageSize)
    result = result[
             (current * pageSize - pageSize):
             current * pageSize
             ]
    return resp.ok(data=result, total=total)


@router.post("/fan/deleteRecord", summary="撤销申请", dependencies=[Depends(get_db)])
async def audit_fan_info(del_list: list) -> Any:
    for id in del_list:
        fan = await FanUpdateRecord.single_by_id(id)
        model = fan['model']
        figNum = fan['figNum']
        version = fan['version']
        fileDir = '/psad/' + 'fan/' + model
        fileNamePrefix = model + '-' + figNum + '-' + version
        # print('fileNamePrefix')
        # print(fileNamePrefix)
        try:
            # 刪除文件
            # if os.path.exists(fileDir):
            #     remove_dir(fileDir)
            # print(fileDir+' deleted')
            if not os.path.exists(fileDir):
                os.makedirs(fileDir)
            for f in os.listdir(fileDir):
                if (f.find(fileNamePrefix) != -1):
                    print('remove file')
                    print(fileDir + '/' + f)
                    os.remove(fileDir + '/' + f)

            async with db.atomic_async():
                await FileInfo.delete_by_biz_id(id)
                await FanUpdateRecordRelp.delete_by_id(id)
                await AuditRecord.del_by_audit_bizId(id)
                await PerfData.del_perf_data(del_list)

                result = await FanUpdateRecord.del_fan(del_list)
                # print(result)
                # await FileInfo.delete_by_biz_id(get_save_bizeId(model, figNum, version))
        except Exception as e:
            print(e)

            return resp.fail(resp.DataDestroyFail, detail=str(e))
    if result != len(del_list):
        return resp.fail(resp.DataDestroyFail.set_msg('删除条数：' + str(result)))
    return resp.ok(data=result)


@router.post("/fan/deleteAuditRecord", summary="撤销申请", dependencies=[Depends(get_db)])
async def audit_fan_info(
        req: sys_fan_schema.FanAudit
) -> Any:
    item_dict = dict(req)
    async with db.atomic_async():
        pass


@router.post("/fan/queryUpdateFansOriginFan", summary="查找审核风机信息的原风机表信息", dependencies=[Depends(get_db)])
async def query_update_fans_origin_fan(
        id: str
) -> Any:
    # id = req['id']
    try:
        async with db.atomic_async():
            record = await FanUpdateRecordRelp.query_by_id(id)
            print('record')
            print(record)
            fanId = record['fanId']
            result = await Fan.single_by_id(fanId)
            # result = await  FanUpdateRecord.single_by_id(id)
            if result is None:
                return resp.fail(resp.DataNotFound)
    except Exception as e:
        return resp.fail(resp.DataNotFound, detail=str(e))

    model = result['model']
    result['img3d'] = img_str_to_url_list(result['img3d'])
    # bizId = get_save_bizeId(result['model'],result['figNum'],result['version'])
    bizId = result['id']
    result['img3d'] = await FileInfo.fuzzy_query({'bizId': bizId, 'bizType': 'img3d'})
    # result['img_outline'] = img_str_to_url_list(result['img_outline'])

    tempFileNameDict = {}
    for fileId in fileNameDict:
        fileName = get_file_name(
            model, result['figNum'], result['version'], fileId)
        # print('fileName')
        # print(fileName)
        tempFileNameDict[fileId] = get_url(
            'fan', model, fileName)

    result["technicalFile"] = tempFileNameDict
    result["outlineFile"] = result["technicalFile"]["outlineFile"]
    result["technicalFile"].pop('outlineFile')
    result["technicalFile"].pop('img3d')
    result["aerodynamicSketch"] = result["technicalFile"]["aerodynamicSketch"]
    result["technicalFile"].pop('aerodynamicSketch')

    result['technicalFile']['labReport'] = await FileInfo.fuzzy_query({'bizId': bizId, 'bizType': 'labReport'})
    result['technicalFile']['designSpecification'] = await FileInfo.fuzzy_query(
        {'bizId': bizId, 'bizType': 'designSpecification'})
    result['outlineFile'] = await FileInfo.fuzzy_query({'bizId': bizId, 'bizType': 'outlineFile'})
    result['aerodynamicSketch'] = await FileInfo.fuzzy_query({'bizId': bizId, 'bizType': 'aerodynamicSketch'})
    # 检查“风机型号”键是否重复
    fanList = await async_db.execute(
        Fan.select().where(Fan.model == model).dicts())
    fanList = list(fanList)
    if len(fanList) > 1:
        isCopy = 'copy'
    else:
        isCopy = None
    result['type'] = isCopy
    # for item in ['imgMain', 'imgOutline']:
    #     path = get_url('fan',  model,  item)
    #     result["imagePath"].append(path)
    result['reason'] = record['remark']
    return resp.ok(data=result)


@router.post("/fan/addAudit", summary="审核风机信息", dependencies=[Depends(get_db)])
async def audit_fan_info(
        req: sys_fan_schema.FanAudit,
        userPerms: Userinfo = Depends(deps.get_current_user_perm)
) -> Any:
    item_dict = dict(req)

    try:
        # if True:
        async with db.atomic_async():
            result = await async_db.execute(
                FanUpdateRecord.select().where(FanUpdateRecord.id == req.auditBizId).dicts())
            recordFan = list(result)[0]
            print(recordFan)
            old_state = recordFan['status']
            new_state = req.result
            # 草稿=》通过
            if old_state == 'audit':
                if '/fan/5:audit' not in userPerms:
                    return resp.fail(resp.Unauthorized.set_msg('操作无权限！'))
                item_dict['auditType'] = 'fanAddAudit'
                # ---检查是否与主表“风机型号-图号-版本号”主键是否重复---
                if req.result == 'pass':
                    new_state = 'pass'
                    fanList = await async_db.execute(
                        Fan.select().where(Fan.model == recordFan['model'], Fan.figNum == recordFan['figNum'],
                                           Fan.version == recordFan['version']).dicts())
                    fanList = list(fanList)
                    if len(fanList) >= 1:
                        return resp.fail(resp.DataStoreFail.set_msg('该风机型号-图号-版本号已存在！'))
                    else:
                        recordFan['status'] = req.result
                # ---检查是否与主表“风机型号-图号-版本号”主键是否重复---

                elif req.result == 'rejected':
                    new_state = 'rejected'
                    recordFan['status'] = req.result
                updateFan = dict_to_model(FanUpdateRecord, recordFan)
                await FanUpdateRecord.update_fan(updateFan)
                item_dict['oldState'] = old_state
                item_dict['newState'] = new_state
                await AuditRecord.add_audit_record(item_dict)

                if req.result == 'pass':
                    newFanId = uuid.uuid1()
                    # recordFan['id'] = str(newFanId)

                    # 风机信息添加到正式表
                    await Fan.add_fan_by_dict(recordFan)
                    version1 = await async_db.execute(
                        FanUpdateRecord.select().where(FanUpdateRecord.model == recordFan['model']).dicts())
                    version1 = len(list(version1))
                    relpRecord = await FanUpdateRecordRelp.query_by_id(req.auditBizId)
                    if relpRecord is None:
                        await FanUpdateRecordRelp.add(
                            {'id': req.auditBizId, 'type': 'add', 'version': version1, 'fanId': recordFan['id']})
                    elif relpRecord['type'] == 'copy':

                        pass

                    # ---审核通过,同步更新同型号风机的基本信息---
                    updateFanList = await Fan.select_by_model(recordFan['model'])
                    del recordFan['figNum']
                    del recordFan['version']
                    for item in updateFanList:
                        recordFan['id'] = item['id']
                        recordFan['updateAt'] = datetime.strftime(datetime.now(pytz.timezone('Asia/Shanghai')),
                                                                  '%Y-%m-%d %H:%M:%S')
                        recordFan['updateBy'] = req.userId
                        updateFan = dict_to_model(Fan, recordFan)
                        await Fan.update_fan(updateFan)
                    # ---审核通过,同步更新同型号风机的基本信息---
            # 领导审核
            if old_state == 'auditByLead':
                if '/fan/5:auditByLead' not in userPerms:
                    return resp.fail(resp.Unauthorized.set_msg('操作无权限！'))
                item_dict['auditType'] = 'fanAlterAudit'
                if req.result == 'pass':
                    # new_state = 'pass'
                    # recordFan['status'] = 'pass'
                    new_state = 'auditAlter'
                    recordFan['status'] = 'auditAlter'
                    updateFan = dict_to_model(FanUpdateRecord, recordFan)
                    await FanUpdateRecord.update_fan(updateFan)
                    await Fan.update_fan(updateFan)
                    item_dict['oldState'] = old_state
                    item_dict['newState'] = new_state
                    await AuditRecord.add_audit_record(item_dict)
                    # new_state = 'auditByLead'
                    # recordFan['status'] = 'auditByLead'
                elif req.result == 'rejected':
                    new_state = 'rejectedAlter'
                    recordFan['status'] = 'rejectedAlter'
                    recordFan['id'] = req.auditBizId
                    updateFan = dict_to_model(FanUpdateRecord, recordFan)
                    await FanUpdateRecord.update_fan(updateFan)
                    item_dict['oldState'] = old_state
                    item_dict['newState'] = new_state
                    await AuditRecord.add_audit_record(item_dict)
            # 数据管理审核
            if old_state == 'auditAlter':
                if '/fan/5:auditAlter' not in userPerms:
                    return resp.fail(resp.Unauthorized.set_msg('操作无权限！'))
                item_dict['auditType'] = 'fanAlterAudit'
                if req.result == 'pass':
                    new_state = 'pass'
                    recordFan['status'] = 'pass'
                    updateFan = dict_to_model(FanUpdateRecord, recordFan)
                    await FanUpdateRecord.update_fan(updateFan)
                    tempRecord = await FanUpdateRecordRelp.query_by_id(req.auditBizId)
                    fanId = tempRecord['fanId']
                    result = await Fan.del_fan([fanId])
                    print('result')
                    print(result)
                    await Fan.add_fan_by_dict(recordFan)
                    originFanIdRecord = await async_db.execute(
                        FanUpdateRecordRelp.select().where(FanUpdateRecordRelp.fanId == fanId).dicts())
                    originFanIdRecord = list(originFanIdRecord)
                    for item in originFanIdRecord:
                        originUpdateRecord = await async_db.execute(
                            FanUpdateRecord.select().where(FanUpdateRecord.id == item['id']).dicts())
                        originUpdateRecord = list(originUpdateRecord)
                        for ud in originUpdateRecord:
                            if ud['id'] == recordFan['id']:
                                continue
                            if ud['status'] == 'pass':
                                ud['status'] = 'passed'
                                # ud['updateAt'] = datetime.strftime(datetime.now(pytz.timezone('Asia/Shanghai')),
                                #                                   '%Y-%m-%d %H:%M:%S')
                                ud = dict_to_model(FanUpdateRecord, ud)
                                await async_db.update(ud)
                        item['fanId'] = recordFan['id']
                        item['updateAt'] = datetime.strftime(datetime.now(pytz.timezone('Asia/Shanghai')),
                                                             '%Y-%m-%d %H:%M:%S')
                        item = dict_to_model(FanUpdateRecordRelp, item)
                        await async_db.update(item)
                    item_dict['oldState'] = old_state
                    item_dict['newState'] = new_state
                    await AuditRecord.add_audit_record(item_dict)
                    # new_state = 'auditByLead'
                    # recordFan['status'] = 'auditByLead'

                    # ---审核通过,同步更新同型号风机的基本信息---
                    updateFanList = await Fan.select_by_model(recordFan['model'])
                    del recordFan['figNum']
                    del recordFan['version']
                    for item in updateFanList:
                        recordFan['id'] = item['id']
                        recordFan['updateAt'] = datetime.strftime(datetime.now(pytz.timezone('Asia/Shanghai')),
                                                                  '%Y-%m-%d %H:%M:%S')
                        recordFan['updateBy'] = req.userId
                        updateFan = dict_to_model(Fan, recordFan)
                        await Fan.update_fan(updateFan)
                    # ---审核通过,同步更新同型号风机的基本信息---

                elif req.result == 'rejected':
                    new_state = 'rejectedAlter'
                    recordFan['status'] = 'rejectedAlter'
                    recordFan['id'] = req.auditBizId
                    updateFan = dict_to_model(FanUpdateRecord, recordFan)
                    await FanUpdateRecord.update_fan(updateFan)
                    item_dict['oldState'] = old_state
                    item_dict['newState'] = new_state
                    await AuditRecord.add_audit_record(item_dict)

    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('该风机型号-图号-版本号已存在！'), detail=str(e))
    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok()


@router.post("/getAuditRecord", summary="查询最新风机审核记录信息", dependencies=[Depends(get_db)])
async def audit_fan_info(
        req: sys_fan_schema.queryAuditRecord
) -> Any:
    # item_dict = dict(req)
    try:
        result = await AuditRecord.select_last_record(req.auditBizId, req.auditType)
    except Exception as e:
        return resp.fail(resp.DataNotFound, detail=str(e))
    return resp.ok(data=result)


@router.post("/fan/getFanVersionData", summary="任意字段筛选风机型号", name="", dependencies=[Depends(get_db)])
async def get_fan_version_data(
        item_dict: dict
) -> Any:
    id = item_dict['id']

    try:
        result = await FanUpdateRecordRelp.query_by_fan_id(id)
    except Exception as e:
        return resp.fail(resp.DataNotFound, detail=str(e))
    return resp.ok(data=result)
