'''
Author: 嘉欣 罗 2592734121@qq.com
Date: 2022-12-23 10:54:58
LastEditors: Please set LastEditors
LastEditTime: 2023-05-11 09:02:57
FilePath: \psad-backend\api\v1\fan.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import re
import time as time1
import ast
import requests
import threading
from datetime import datetime
import uuid
from filecmp import cmp
import json
import math
import pathlib
from pydantic.dataclasses import dataclass
import glob
import os
from typing import Any, Dict, List, Union
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from pymysql import IntegrityError
from api.v1.file import get_save_dir
from api.v1.perf import func_get_perf_data_by_fan_id, get_perf_data
from common import deps
from common.session import get_db, async_db

from core import security
from models.fan import Fan, FanCategory, FanCoolObject
from models.update_fan_record import FanUpdateRecord, FanUpdateRecordRelp
from models.fan_perf_data import PerfData
from models.user import Userinfo
from models.file_info import FileInfo
from models.audit import AuditRecord
from schemas.response import resp
from schemas.request import sys_fan_schema
from playhouse.shortcuts import model_to_dict

from fastapi import status as http_status
from fastapi.responses import JSONResponse, Response, FileResponse
from playhouse.shortcuts import model_to_dict
from utils.calculation import fit_perf_data, fit_perf_data_by_motorSpeed, get_specific_speed
from utils.file import cmp_file, get_file_name, get_save_file_name, get_url, img_str_to_url_list, fileNameDict, \
    save_file_info
from utils.tools_func import name_convert_to_camel, name_convert_to_snake, remove_dir, validateStr, write_excel_xls, \
    convert_arr
from peewee import fn, IntegrityError
import numpy as np
from common.session import db
from playhouse.shortcuts import model_to_dict, dict_to_model
from utils.tools_func import rolePremission, tz
from utils.file import up_file

import pytz

# import matplotlib.pyplot as plt
router = APIRouter()


def get_save_bizeId(model: str, figNum: str, version: str):
    return model + '-' + figNum + '-' + version


#
@router.get("/tree", summary="获取风机类型及风机型号", name="", dependencies=[Depends(get_db)])
async def get_fan_category_and_model() -> Any:
    result = await  Fan.group_by_category()
    # result =await FanCategory.select_group_all()
    # result = list(db)
    if result:
        return resp.ok(data=result)
    else:
        return resp.ok(data={})


@router.get("/cool/queryAll", summary="获取所有风机类型", dependencies=[Depends(get_db)], name="")
async def get_fan_cool_object_with_id() -> Any:
    db = await FanCoolObject.select_all()
    result = list(db)
    if result:
        return resp.ok(data=result)
    else:
        return resp.ok(data=[])


#
@router.get("/cool/all", summary="获取所有冷却对象字段", name="", dependencies=[Depends(get_db)])
async def get_fan_cool_object() -> Any:
    db = await FanCoolObject.select_all()
    # db = list(db)

    result = []
    for item in db:
        result.append(item['name'])
    if result:
        return resp.ok(data=result)
    else:
        return resp.ok(data=[])


def get_perf_line_equation(perf_data: list, xField: str, yField: str):
    # print('perf_data')
    # print(perf_data)
    if len(perf_data) == 0:
        return [0, 0, 0]
    # 驼峰命名转下划线

    # 初始化data结构
    data = {xField: [], yField: []}

    # 获取字段对应数据
    for record in perf_data:
        data[xField].append(record[xField])
        data[yField].append(record[yField])

    # 计算方程
    x = data[xField]
    result = []
    y = data[yField]
    # print('x:')
    # print(xField)
    # print('y:')
    # print(yField)
    an = np.polyfit(x, y, 2)
    result = an
    print('result')
    print(result)
    return result


def range_exclusion(rangeList: list, excludeFiled: str, data: list):
    # print('rangeList')
    # print(rangeList)
    del_index = []
    for i in range(len(data)):
        # print('data[i][excludeFiled]')
        # print(data[i][excludeFiled])
        if data[i][excludeFiled] == 0:
            pass
        elif rangeList[0] > data[i][excludeFiled] or rangeList[1] < data[i][excludeFiled]:
            del_index.append(i)
    # 删除超出range的风机
    temp = []
    print(del_index)
    for i in range(len(data)):
        if i not in del_index:
            temp.append(data[i])
    result = temp
    return result

# , dependencies= [Depends(get_db)]

@router.post("/show", summary="任意字段筛选风机型号", name="", dependencies=[Depends(get_db)])
async def show_fans(
        # item_dict:dict
        req: sys_fan_schema.FanQuery,
        userPerms: Userinfo = Depends(deps.get_current_user_perm)
) -> Any:
    print('req.status')
    print(req.status)
    # /fan/1:auth_show_all
    item_dict = dict(req)
    # 通过性能数据拟合曲线计算
    # print('req.sortRange')
    # print(req.sortRange)
    if req.sortRange != None:

        if req.sort:
            xField = req.sortParam2
            yField = req.sortParam1
        else:
            xField = req.sortParam1
            yField = req.sortParam2

        x = item_dict[xField]
        y = item_dict[yField]
        r0 = float(req.sortRange[0])
        r1 = float(req.sortRange[1])
        range = [y - y * r0 / 100, y + y * r1 / 100]

        # item_dict直接在数据库中查询 so 需剔除需要根据曲线计算的字段
        item_dict[xField] = None
        item_dict[yField] = None

    # 根据其他条件初次筛选
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
    if '/fan/4' not in userPerms:
        item_dict['status'] = ['pass']
    else:
        item_dict['status'] = ['pass']
    try:
        result = await Fan.fuzzy_query_by_dict(item_dict, False)
    except Exception as e:
        # print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    if req.sortRange != None:
        i = 0
        for fan in result:
            # print(fan['model'])
            try:
                # lock = threading.Lock()
                # lock.acquire()
                perfData = await PerfData.get_perf_data_by_fan_id(fan['id'])
                # lock.release()
            except Exception as e:
                return resp.fail(resp.DataNotFound, detail=str(e))
            fan['originMotorSpeed'] = perfData[0]['motorSpeed']
            # get方程系数

            an = get_perf_line_equation(
                perfData, xField, yField)
            # y = fan[name_convert_to_snake(yField)]
            # print('xxxxx')
            # print(x)
            result[i]['sort' + yField] = float(format(an[0] * x ** 2 + an[1]
                                                      * x + an[2], '.3f' if yField == 'flowRate' else '.1f'))
            print('yyyy')
            print(y)
            print("result[i]['sort'+yField]")
            print(result[i]['sort' + yField])
            # result[i]['sortField'] = abs(result[i]['sort' + yField] - y)
            result[i]['sortField'] = abs((result[i]['sort' + yField] - y) / y * 100)

            result[i]['deviation' + yField] = float(format(
                (result[i]['sort' + yField] - y) / y * 100, '.1f'))
            result[i]['search' + xField] = x
            field = ['flowRate', 'fullPressure', 'staticPressure', 'shaftPower']
            field.pop(field.index(xField))
            field.pop(field.index(yField))
            for f in field:
                an = get_perf_line_equation(
                    perfData, xField, f)
                result[i]['sort' + f] = float(format(an[0] * x ** 2 + an[1]
                                                     * x + an[2], '.3f' if f == 'flowRate' else '.1f'))
                # result[i]['sortField'] = abs(result[i]['sort' + yField] - y)
                result[i]['sortField'] = abs((result[i]['sort' + yField] - y) / y * 100)
            i = i + 1

        result = range_exclusion(range, 'sort' + yField, result)

        # sort 是应用在 list 上的方法，sorted 可以对所有可迭代的对象进行排序操作。reverse = True 降序 ， reverse = False 升序（默认
        # .__getitem__ 使用索引访问元素
        sortFlag = False
        result = sorted(result, key=lambda e: e.__getitem__(
            'sortField'), reverse=sortFlag)
    # ---去除不在最小值最大值区间内的start---
    delList = []
    i = 0
    for item in result:
        if req.flowRateBetween:
            if not (req.flowRateBetween[0] <= item['flowRate'] and item['flowRate'] <= req.flowRateBetween[1]):
                delList.append(i)
        if req.fullPressureBetween:
            if not (req.fullPressureBetween[0] <= item['fullPressure'] and item['fullPressure'] <=
                    req.fullPressureBetween[1]):
                delList.append(i)
        if req.motorSpeedBetween:
            if not (req.motorSpeedBetween[0] <= item['motorSpeed'] and item['motorSpeed'] <= req.motorSpeedBetween[1]):
                delList.append(i)
        if req.shaftPowerBetween:
            if not (req.shaftPowerBetween[0] <= item['shaftPower'] and item['shaftPower'] <= req.shaftPowerBetween[1]):
                delList.append(i)
        if req.efficiencyBetween:
            if not (req.efficiencyBetween[0] <= item['efficiency'] and item['efficiency'] <= req.efficiencyBetween[1]):
                delList.append(i)
        i = i + 1
    i = 0
    temp = []
    for item in result:
        if i in delList:
            i = i + 1
            continue
        else:
            temp.append(item)
        i = i + 1
    result = temp
    # ---去除不在最小值最大值区间内的end---
    # TODO：[{}]排序
    # 单级排序，仅按照score排序
    # result = sorted(result, key=lambda e: e.__getitem__('sort'+yField))
    # 多级排序,先按照'sort'+yField，再按照no排序
    # result = sorted(result, key=lambda e:(e.__getitem__('sort'+yField), e.__getitem__('sortField')))

    total = len(result)
    # 分页
    current = int(req.current)
    pageSize = int(req.pageSize)
    result = result[
             (current * pageSize - pageSize):
             current * pageSize
             ]
    return resp.ok(data=result, total=total)


# , dependencies= [Depends(get_db)]
@router.post("/change/show", summary="变形设计任意字段查询风机", name="筛选风机")
async def change_show_fans( req: sys_fan_schema. FanChangeQuery,
) -> Any:
    item_dict = dict(req)
    item_dict['status'] = 'pass'
    # TODO:category筛选
    try:
        result = await Fan.change_fuzzy_query_by_dict(
            item_dict, req.limitCategoryId, False)
        # return resp.ok(data=result)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    delList = []
    i = 0
    for fan in result:
        fan['showModel'] = fan['model']
        fan['changeModel'] = fan['model'] + '-' + fan['figNum'] + '-' + fan['version']
        fan['changeId'] = fan['id']
        perfData = await func_get_perf_data_by_fan_id(fan['id'])
        fan['perf'] = perfData
        # 风机基本信息转速 与 实验数据转速不一致时应取实验数据转速

        if len(perfData) == 0:
            delList.append(i)
        else:
            motorSpeed = perfData['motorSpeed'][0]

            fan['motorSpeed'] = motorSpeed
        i = i + 1
    temp = []
    i = 0
    for fan in result:
        if i in delList:
            i = i + 1
            continue
        else:
            temp.append(fan)
    result = temp
    # 输入了转速 先按比转速排序
    if req.specificSpeed != None:
        print('输入了转速 先按比转速排序')
        sortFlowRate = req.sortFlowRate
        sortMotorSpeed = req.sortMotorSpeed
        # sortPressure = req[req.pressureField]
        pressureField = req.pressureField
        specificSpeed = req.specificSpeed

        # 删除没有性能曲线数据的风机
        # 删除要求比转速不在风机最小比转速/最大比转速区间的风机
        i = 0
        delIndex = []
        for fan in result:
            if len(perfData) == 0:
                delIndex.append(i)
            else:
                sortedBySpecificSpeed = sorted(perfData['specificSpeed'])  # 以默认升序排列
                specificSpeedMin = sortedBySpecificSpeed[0]
                specificSpeedMax = sortedBySpecificSpeed[-1]

                if specificSpeed < specificSpeedMin or specificSpeed > specificSpeedMax:
                    delIndex.append(i)
                else:
                    result[i]['specificSpeedMin'] = specificSpeedMin
                    result[i]['specificSpeedMax'] = specificSpeedMax
            if pressureField == 'fullPressure' and fan['fullPressure']:
                pressureDeviation = (fan['fullPressure'] - req.sortFullPressure
                                     ) / req.sortFullPressure
                fan['pressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
            elif pressureField == 'staticPressure' and fan['staticPressure']:
                pressureDeviation = (fan['staticPressure'] - req.sortStaticPressure
                                     ) / req.sortStaticPressure
                fan['pressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
            i = i + 1

        # 删除超出range的风机
        temp = []
        for i in range(len(result)):
            if i not in delIndex:
                temp.append(result[i])
        result = temp

    # 转速变动 换算 流量、压力、功率
    if req.sortMotorSpeed:
        print('转速变动 换算 流量、压力、功率')
        sortMotorSpeed = req.sortMotorSpeed
        for fan in result:
            motorSpeed = fan['motorSpeed']
            perfData = fan['perf']
            flowRateData = perfData['flowRate']
            fullPressureData = perfData['fullPressure']
            staticPressureData = perfData['staticPressure']
            # pressureData = perfData[req.pressureField]
            shaftPowerData = perfData['shaftPower']
            tempPerfData = fit_perf_data_by_motorSpeed(
                flowRateData, fullPressureData, staticPressureData, shaftPowerData, sortMotorSpeed, motorSpeed)
            perfData['flowRate'] = tempPerfData['flowRate']
            perfData['fullPressure'] = tempPerfData['fullPressure']
            perfData['staticPressure'] = tempPerfData['staticPressure']
            perfData['shaftPower'] = tempPerfData['shaftPower']
            fan['perf'] = perfData

    # 存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机
    if req.limitField == 'flowRate':
        print('存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机')
        if req.sortFullPressure:
            sortPressure = req.sortFullPressure
        elif req.sortStaticPressure:
            sortPressure = req.sortStaticPressure
        sortFlowRate = req.sortFlowRate
        # 计算给定压力的误差范围
        pressureRange = [(1 - req.min / 100) * sortPressure,
                         (1 + req.max / 100) * sortPressure]
        appendFan = []
        for fan in result:
            if req.sortMotorSpeed:
                fan['similarMotorSpeed'] = req.sortMotorSpeed
            perfData = fan['perf']

            # 取不同叶轮直径 流量 压力 换算
            impellerDiameter = fan['impellerDiameter']
            flowRateData = perfData['flowRate']
            # fP = perfData['fullPressure']
            pressureData = perfData[req.pressureField]
            # fP = perfData[req.pressureField]
            impellerDiaRange = [0, 0]
            # 通过这个函数取到相似完直径的区间
            impellerDiaRange[0] = approach_the_boundary(
                sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[0], True)
            impellerDiaRange[1] = approach_the_boundary(
                sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[1], False)
            fan['flowRate'] = sortFlowRate

            impellerDiaRange = sorted(impellerDiaRange)
            fan['impellerDiameterRange'] = impellerDiaRange
            # 对存在两段范围符合要求的风机的处理
            # an为拟合出来二次曲线的系数列表
            an = fit_perf_data(
                flowRateData, pressureData, impellerDiaRange[0], impellerDiameter)
            x1 = -an[1] / (2 * an[0])
            y1 = x1 * x1 * an[0] + x1 * an[1] + an[2]
            an = fit_perf_data(
                flowRateData, pressureData, impellerDiaRange[1], impellerDiameter)
            x2 = -an[1] / (2 * an[0])
            y2 = x2 * x2 * an[0] + x2 * an[1] + an[2]
            # 限定的流量不在计算区间内
            if (x1 > sortFlowRate and x2 < sortFlowRate):
                print("选型出现了未考虑到的情况！")
                pass
            if (x1 < sortFlowRate and x2 > sortFlowRate and (y1 > pressureRange[1] or y2 > pressureRange[1])):
                impellerD = impellerDiaRange[0]
                # 遍历直径区间，拟合每一个直径相似设计后的压力
                while impellerD < impellerDiaRange[1]:
                    p = fit_perf_data(
                        flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                    if p < pressureRange[0] or p > pressureRange[1]:
                        break
                    impellerD = impellerD + 1
                tempImpellerDiaRange1 = [impellerDiaRange[0], impellerD]
                impellerD = impellerDiaRange[1]
                while impellerD > impellerDiaRange[0]:
                    p = fit_perf_data(
                        flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                    if p < pressureRange[0] or p > pressureRange[1]:
                        break
                    impellerD = impellerD - 1
                tempImpellerDiaRange2 = [impellerD, impellerDiaRange[1]]
                fan['impellerDiameterRange'] = tempImpellerDiaRange1
                temp = {}
                for key in fan:
                    temp[key] = fan[key]
                temp['impellerDiameterRange'] = tempImpellerDiaRange2
                appendFan.append(temp)

            # 存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机
        if req.limitField == 'flowRate':
            print('存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机')
            if req.sortFullPressure:
                sortPressure = req.sortFullPressure
            elif req.sortStaticPressure:
                sortPressure = req.sortStaticPressure
            sortFlowRate = req.sortFlowRate
            # pressureRange => impellerDiameterRange
            pressureRange = [(1 - req.min / 100) * sortPressure,
                             (1 + req.max / 100) * sortPressure]

            appendFan = []
            for fan in result:
                if req.sortMotorSpeed:
                    fan['similarMotorSpeed'] = req.sortMotorSpeed
                perfData = fan['perf']

                # 取不同叶轮直径 流量 压力 换算
                impellerDiameter = fan['impellerDiameter']
                flowRateData = perfData['flowRate']
                # fP = perfData['fullPressure']
                pressureData = perfData[req.pressureField]
                # fP = perfData[req.pressureField]
                impellerDiaRange = [0, 0]
                # print('------- '+fan['model'] + 'start -----------------')
                # 如果pressureBoundary为最小边界，为true, 如果pressureBoundary为最大边界，为false
                impellerDiaRange[0] = approach_the_boundary(
                    sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[0], True)
                impellerDiaRange[1] = approach_the_boundary(
                    sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[1], False)

                fan['flowRate'] = sortFlowRate

                # impellerDiameterMedian = '{:.0f}'.format(impellerDiameterMedian)

                impellerDiaRange = sorted(impellerDiaRange)
                fan['impellerDiameterRange'] = impellerDiaRange
                # 对存在两段范围符合要求的风机的处理
                an = fit_perf_data(
                    flowRateData, pressureData, impellerDiaRange[0], impellerDiameter)
                x1 = -an[1] / (2 * an[0])
                y1 = x1 * x1 * an[0] + x1 * an[1] + an[2]
                an = fit_perf_data(
                    flowRateData, pressureData, impellerDiaRange[1], impellerDiameter)
                x2 = -an[1] / (2 * an[0])
                y2 = x2 * x2 * an[0] + x2 * an[1] + an[2]
                if (x1 > sortFlowRate and x2 < sortFlowRate):
                    print("选型出现了未考虑到的情况！")
                    pass
                if (x1 < sortFlowRate and x2 > sortFlowRate and (y1 > pressureRange[1] or y2 > pressureRange[1])):
                    impellerD = impellerDiaRange[0]
                    while impellerD < impellerDiaRange[1]:
                        p = fit_perf_data(
                            flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                        if p < pressureRange[0] or p > pressureRange[1]:
                            break
                        impellerD = impellerD + 1
                    # print('impellerD 111')
                    # print(impellerD)
                    tempImpellerDiaRange1 = [impellerDiaRange[0], impellerD]
                    # print('tempImpellerDiaRange')
                    # print(tempImpellerDiaRange1)
                    impellerD = impellerDiaRange[1]
                    while impellerD > impellerDiaRange[0]:
                        p = fit_perf_data(
                            flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                        if p < pressureRange[0] or p > pressureRange[1]:
                            break
                        impellerD = impellerD - 1
                    # print('impellerD 2222')
                    # print(impellerD)
                    tempImpellerDiaRange2 = [impellerD, impellerDiaRange[1]]
                    # print('tempImpellerDiaRange')
                    # print(tempImpellerDiaRange2)

                    fan['impellerDiameterRange'] = tempImpellerDiaRange1
                    temp = {}
                    for key in fan:
                        temp[key] = fan[key]
                    temp['impellerDiameterRange'] = tempImpellerDiaRange2
                    appendFan.append(temp)

        i = 1
        for item in appendFan:
            # item['model'] = '('+str(i)+')' + item['model']
            item['showModel'] = '(' + str(i) + ')' + item['model']
            item['similarModel'] = '(' + str(i) + ')' + item['model'] + '-' + item['figNum'] + '-' + item['version']
            item['similarId'] = '(' + str(i) + ')' + item['id']
            result.append(item)
            i = i + 1
        # appendFan = []
        req.sortFields = ['pressureDeviation',
                          'impellerDiaDeviation'] + req.sortFields
    delIndex = []
    if req.limitField == 'flowRate':
        for i in range(len(result)):
            fan = result[i]
            if fan['impellerDiameterRange'][0] == fan['impellerDiameterRange'][1]:
                delIndex.append(i)

    # 用户输入的叶轮直径筛选
    if req.impellerDiameterMin and req.impellerDiameterMax:
        for i in range(len(result)):
            fan = result[i]
            if req.limitField == 'flowRate':
                # 存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机
                fan['impellerDiameterRange']
                minNum = max(req.impellerDiameterMin,
                             fan['impellerDiameterRange'][0])
                maxNum = min(req.impellerDiameterMax,
                             fan['impellerDiameterRange'][1])
                if minNum > maxNum:
                    delIndex.append(i)
                    continue
                if req.impellerDiameterMin > fan['impellerDiameterRange'][0]:
                    fan['impellerDiameterRange'][0] = req.impellerDiameterMin
                if req.impellerDiameterMax < fan['impellerDiameterRange'][1]:
                    fan['impellerDiameterRange'][1] = req.impellerDiameterMax

            elif req.limitField == 'unLimited':

                if not (req.impellerDiameterMin <= fan['impellerDiameter'] and fan[
                    'impellerDiameter'] <= req.impellerDiameterMax):
                    # print('del i')
                    delIndex.append(i)
            i = i + 1
    # 删除超出range的风机
    temp = []
    # print(delIndex)
    for i in range(len(result)):
        if i not in delIndex:
            temp.append(result[i])
    result = temp

    delFan = []
    # 计算需要展示的信息
    if req.limitField == 'flowRate':
        i = 0
        for fan in result:

            perfData = fan['perf']
            impellerDiaRange = fan['impellerDiameterRange']
            impellerDiameter = fan['impellerDiameter']
            # print("impellerDiaRange")
            # print(impellerDiaRange)
            impellerDiaMedian = float('{:.0f}'.format(
                0.5 * (impellerDiaRange[0] + impellerDiaRange[1])))
            fan['impellerDiameterMedian'] = float(impellerDiaMedian)
            if req.impellerDiameterRatioMin and req.impellerDiameterRatioMax:
                # print(impellerDiaRange)
                impellerDiaRangeList = range(impellerDiaRange[0], impellerDiaRange[1] + 1)
                impellerDiameterRatioRange = [req.impellerDiameterRatioMin, req.impellerDiameterRatioMax]
                # 叶轮直径比例修改在这里,计算完之后求交集

                if len(impellerDiameterRatioRange) == 0:
                    fan['impellerDiameterRange'] = []
                    fan['impellerDiameterMedian'] = None
                    break
                else:
                    # 计算比例对应的直径区间
                    impellerDiameterRatioRange = [math.ceil(req.impellerDiameterRatioMin * impellerDiameter),
                                                  math.ceil(req.impellerDiameterRatioMax * impellerDiameter)]
                    impellerDiameterRatioRangeList = range(impellerDiameterRatioRange[0],
                                                           impellerDiameterRatioRange[1] + 1)
                    # print(impellerDiameterRatioRange)
                    # 求交集
                    impellerDiameterRatioRangeList = list(
                        set(impellerDiaRangeList).intersection(set(impellerDiameterRatioRangeList)))
                    # print(impellerDiameterRatioRangeList)
                    impellerDiameterRatioRangeList.sort()
                    # print(impellerDiameterRatioRangeList)

                    if impellerDiameterRatioRangeList == []:
                        impellerDiaRange = []
                        fan['impellerDiameterRange'] = impellerDiaRange
                        fan['impellerDiameterMedian'] = None
                        delFan.append(i)
                        i = i + 1
                        continue
                    else:
                        impellerDiaRange = [impellerDiameterRatioRangeList[0], impellerDiameterRatioRangeList[-1]]
                        fan['impellerDiameterRange'] = impellerDiaRange
                        impellerDiaMedian = float('{:.0f}'.format(0.5 * (impellerDiaRange[0] + impellerDiaRange[1])))
                        fan['impellerDiameterMedian'] = float(impellerDiaMedian)
            # # print(fan['impellerDiameterMedian'])
            # print("impellerDiaMedian")
            # print(impellerDiaMedian)
            # impellerDiaMedian = fan['impellerDiameterMedian']
            # sortFlowRate = req.sortFlowRate
            # if req.pressureField == 'fullPressure':
            # if len(impellerDiameterRatioRangeList) != 0:
            if True:
                fR = perfData['flowRate']
                fP = perfData['fullPressure']
                # print('fP')
                # print(fP)
                # 计算相似完的全压
                similarFullPressure = fit_perf_data(
                    fR, fP, impellerDiaMedian, impellerDiameter, sortFlowRate)

                fan['similarFullPressure'] = similarFullPressure
                fan['fullPressure'] = similarFullPressure

                # 计算直径偏差
                impellerDiaDeviation = (
                                               impellerDiaMedian - impellerDiameter) / impellerDiameter
                fan['impellerDiaDeviation'] = float(
                    '{:.2f}'.format(impellerDiaDeviation))

                # elif req.pressureField == 'staticPressure':
                sP = perfData['staticPressure']
                # print('sP')
                # print(sP)
                # 计算相似完的静压
                similarStaticPressure = fit_perf_data(
                    fR, sP, impellerDiaMedian, impellerDiameter, sortFlowRate)
                fan['similarStaticPressure'] = similarStaticPressure
                fan['staticPressure'] = similarStaticPressure

                # 计算全压的偏差
            if req.pressureField == 'fullPressure':
                pressureDeviation = (similarFullPressure - sortPressure) / \
                                    sortPressure * 100
                fan['fullPressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
                # fan['absPressureDeviation'] = abs(fan['fullPressureDeviation'])
                fan['absPressureDeviation'] = fan['fullPressureDeviation']
            # 计算静压的偏差
            elif req.pressureField == 'staticPressure':
                pressureDeviation = (similarStaticPressure - sortPressure) / \
                                    sortPressure * 100
                fan['staticPressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
                # fan['absPressureDeviation'] = abs(
                #     fan['staticPressureDeviation'])
                fan['absPressureDeviation'] = fan['staticPressureDeviation']
            # req.sortFields.append('absPressureDeviation')
            # if fan['impellerDiameterMedian'] == None or fan['impellerDiameterRange'][0] == [1]:
            #     result.pop(fan)
            # shaftPower计算
            fR = perfData['flowRate']
            sP = perfData['shaftPower']
            #  计算轴功率
            similarShaftPower = fit_perf_data(
                fR, sP, impellerDiaMedian, impellerDiameter, sortFlowRate)
            fan['similarShaftPower'] = similarShaftPower

            fan.pop('perf')
            # print('result2')
            # print(result)
            i = i + 1
    # print(result)
    # print(delFan)
    result = [fan for num, fan in enumerate(result) if num not in delFan]  # 通过枚举删除叶轮直径变化范围为[]的字典
    # 计算排序noise
    i = 0
    for fan in result:
        perfData = await PerfData.get_perf_data_by_model(fan['model'])
        result[i]['noise'] = 0

        # if fan['noise'] is None:
        #     result[i]['noise'] = 0
        i = i + 1

    reverseArr = []
    if len(req.sortFields) != 0:
        for field in req.sortFields:

            if field == 'efficiency':
                reverseArr.append(True)
            if field == 'noise':
                reverseArr.append(False)  # 升序
            if field == 'pressureDeviation':
                reverseArr.append(False)  # 升序
            if field == 'absPressureDeviation':
                reverseArr.append(True)  # 升序
            if field == 'impellerDiaDeviation':
                reverseArr.append(False)  # 升序
    i = 0
    for field in req.sortFields:
        # print(field)

        if len(result) > 0 and field in list(result[0].keys()):
            result = sorted(result, key=lambda e: (
                e.__getitem__(field)), reverse=reverseArr[i])
        i = i + 1
        # if len(req.sortFields) == 2:
    # TODO:双字段排序

    # 分页
    current = int(req.current)
    pageSize = int(req.pageSize)
    total = len(result)
    result = result[
             (current * pageSize - pageSize):
             current * pageSize
             ]
    return resp.ok(data=result, total=total)

@router.post("/similar/show", summary="相似设计任意字段筛选风机型号", name="", dependencies=[Depends(get_db)])
async def similar_show_fans(
        # item_dict:dict
        req: sys_fan_schema.FanSimilarQuery,
) -> Any:
    item_dict = dict(req)
    # 通过性能数据拟合曲线计算
    # 根据其他条件初次筛选
    item_dict['status'] = 'pass'
    # TODO:category筛选
    try:
        result = await Fan.similar_fuzzy_query_by_dict(
            item_dict, req.limitCategoryId, False)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    delList = []
    i = 0
    for fan in result:
        fan['showModel'] = fan['model']
        fan['similarModel'] = fan['model'] + '-' + fan['figNum'] + '-' + fan['version']
        fan['similarId'] = fan['id']
        # print("fan['id']")
        # print(fan['id'])
        perfData = await func_get_perf_data_by_fan_id(fan['id'])
        fan['perf'] = perfData
        # 风机基本信息转速 与 实验数据转速不一致时应取实验数据转速

        if len(perfData) == 0:
            delList.append(i)
        else:
            motorSpeed = perfData['motorSpeed'][0]

            fan['motorSpeed'] = motorSpeed
        i = i + 1
    temp = []
    i = 0
    for fan in result:
        if i in delList:
            i = i + 1
            continue
        else:
            temp.append(fan)
    result = temp
    # 输入了转速 先按比转速排序
    if req.specificSpeed != None:
        print('输入了转速 先按比转速排序')
        sortFlowRate = req.sortFlowRate
        sortMotorSpeed = req.sortMotorSpeed
        # sortPressure = req[req.pressureField]
        pressureField = req.pressureField
        specificSpeed = req.specificSpeed

        # 删除没有性能曲线数据的风机
        # 删除要求比转速不在风机最小比转速/最大比转速区间的风机
        i = 0
        delIndex = []
        for fan in result:
            perfData = fan['perf']
            if len(perfData) == 0:
                delIndex.append(i)
            else:
                sortedBySpecificSpeed = sorted(perfData['specificSpeed'])#以默认升序排列
                specificSpeedMin = sortedBySpecificSpeed[0]
                specificSpeedMax = sortedBySpecificSpeed[-1]
                if specificSpeed < specificSpeedMin or specificSpeed > specificSpeedMax:
                    delIndex.append(i)
                else:
                    result[i]['specificSpeedMin'] = specificSpeedMin
                    result[i]['specificSpeedMax'] = specificSpeedMax
            if pressureField == 'fullPressure' and fan['fullPressure']:
                pressureDeviation = (fan['fullPressure'] - req.sortFullPressure
                                     ) / req.sortFullPressure
                fan['pressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
            elif pressureField == 'staticPressure' and fan['staticPressure']:
                pressureDeviation = (fan['staticPressure'] - req.sortStaticPressure
                                     ) / req.sortStaticPressure
                fan['pressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
            i = i + 1

        # 删除超出range的风机
        temp = []
        for i in range(len(result)):
            if i not in delIndex:
                temp.append(result[i])
        result = temp

    # 转速变动 换算 流量、压力、功率
    if req.sortMotorSpeed:
        print('转速变动 换算 流量、压力、功率')
        sortMotorSpeed = req.sortMotorSpeed
        for fan in result:
            motorSpeed = fan['motorSpeed']
            perfData = fan['perf']
            flowRateData = perfData['flowRate']
            fullPressureData = perfData['fullPressure']
            staticPressureData = perfData['staticPressure']
            # pressureData = perfData[req.pressureField]
            shaftPowerData = perfData['shaftPower']
            tempPerfData = fit_perf_data_by_motorSpeed(
                flowRateData, fullPressureData, staticPressureData, shaftPowerData, sortMotorSpeed, motorSpeed)
            perfData['flowRate'] = tempPerfData['flowRate']
            perfData['fullPressure'] = tempPerfData['fullPressure']
            perfData['staticPressure'] = tempPerfData['staticPressure']
            perfData['shaftPower'] = tempPerfData['shaftPower']
            fan['perf'] = perfData

    # 存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机
    if req.limitField == 'flowRate':
        print('存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机')
        if req.sortFullPressure:
            sortPressure = req.sortFullPressure
        elif req.sortStaticPressure:
            sortPressure = req.sortStaticPressure
        sortFlowRate = req.sortFlowRate

        # pressureRange => impellerDiameterRange
        # 计算给定压力的误差范围
        pressureRange = [(1 - req.min / 100) * sortPressure,
                         (1 + req.max / 100) * sortPressure]
        appendFan = []
        for fan in result:
            if req.sortMotorSpeed:
                fan['similarMotorSpeed'] = req.sortMotorSpeed
            perfData = fan['perf']

            # 取不同叶轮直径 流量 压力 换算
            impellerDiameter = fan['impellerDiameter']
            flowRateData = perfData['flowRate']
            # fP = perfData['fullPressure']
            pressureData = perfData[req.pressureField]
            # fP = perfData[req.pressureField]
            impellerDiaRange = [0, 0]
            # print('------- '+fan['model'] + 'start -----------------')
            # 通过这个函数取到相似完直径的区间
            impellerDiaRange[0] = approach_the_boundary(
                sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[0], True)
            impellerDiaRange[1] = approach_the_boundary(
                sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[1], False)
            fan['flowRate'] = sortFlowRate

            # impellerDiameterMedian = '{:.0f}'.format(impellerDiameterMedian)

            impellerDiaRange = sorted(impellerDiaRange)
            fan['impellerDiameterRange'] = impellerDiaRange
            # 对存在两段范围符合要求的风机的处理
            # an为拟合出来二次曲线的系数列表
            an = fit_perf_data(
                flowRateData, pressureData, impellerDiaRange[0], impellerDiameter)
            x1 = -an[1] / (2 * an[0])
            y1 = x1 * x1 * an[0] + x1 * an[1] + an[2]
            an = fit_perf_data(
                flowRateData, pressureData, impellerDiaRange[1], impellerDiameter)
            x2 = -an[1] / (2 * an[0])
            y2 = x2 * x2 * an[0] + x2 * an[1] + an[2]
            # 限定的流量不在计算区间内
            if (x1 > sortFlowRate and x2 < sortFlowRate):
                print("选型出现了未考虑到的情况！")
                pass
            if (x1 < sortFlowRate and x2 > sortFlowRate and (y1 > pressureRange[1] or y2 > pressureRange[1])):
                impellerD = impellerDiaRange[0]
                # 遍历直径区间，拟合每一个直径相似设计后的压力
                while impellerD < impellerDiaRange[1]:
                    p = fit_perf_data(
                        flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                    if p < pressureRange[0] or p > pressureRange[1]:
                        break
                    impellerD = impellerD + 1
                # print('impellerD 111')
                # print(impellerD)
                tempImpellerDiaRange1 = [impellerDiaRange[0], impellerD]
                # print('tempImpellerDiaRange')
                # print(tempImpellerDiaRange1)
                impellerD = impellerDiaRange[1]
                while impellerD > impellerDiaRange[0]:
                    p = fit_perf_data(
                        flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                    if p < pressureRange[0] or p > pressureRange[1]:
                        break
                    impellerD = impellerD - 1
                # print('impellerD 2222')
                # print(impellerD)
                tempImpellerDiaRange2 = [impellerD, impellerDiaRange[1]]
                # print('tempImpellerDiaRange')
                # print(tempImpellerDiaRange2)

                fan['impellerDiameterRange'] = tempImpellerDiaRange1
                temp = {}
                for key in fan:
                    temp[key] = fan[key]
                temp['impellerDiameterRange'] = tempImpellerDiaRange2
                appendFan.append(temp)
                # print('---------------------------')
                # print('tempImpellerDiaRange1')
                # print(tempImpellerDiaRange1)
                # print('tempImpellerDiaRange2')
                # print(tempImpellerDiaRange2)
                # print(fan['impellerDiameterRange'])
                # print(temp['impellerDiameterRange'])
                # print('---------------------------')

                # tempImpellerDiaRange = [0, 0]
                # tempImpellerDiaRange[0] = approach_the_boundary1(impellerDiaRange[0], impellerD, sortFlowRate,
                #                                                  impellerDiameter, flowRateData, pressureData, pressureRange[0], False)
                # tempImpellerDiaRange[1] = approach_the_boundary1(impellerD, impellerDiaRange[1], sortFlowRate,
                #                                                  impellerDiameter, flowRateData, pressureData, pressureRange[0], True)
                # print('tempImpellerDiaRange')
                # print(tempImpellerDiaRange)

            # 存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机
        if req.limitField == 'flowRate':
            print('存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机')
            if req.sortFullPressure:
                sortPressure = req.sortFullPressure
            elif req.sortStaticPressure:
                sortPressure = req.sortStaticPressure
            sortFlowRate = req.sortFlowRate
            # pressureRange => impellerDiameterRange
            pressureRange = [(1 - req.min / 100) * sortPressure,
                             (1 + req.max / 100) * sortPressure]
            # print('pressureRange')
            # print(pressureRange)
            # result = [result[0]]
            appendFan = []
            for fan in result:
                if req.sortMotorSpeed:
                    fan['similarMotorSpeed'] = req.sortMotorSpeed
                perfData = fan['perf']

                # 取不同叶轮直径 流量 压力 换算
                impellerDiameter = fan['impellerDiameter']
                flowRateData = perfData['flowRate']
                # fP = perfData['fullPressure']
                pressureData = perfData[req.pressureField]
                # fP = perfData[req.pressureField]
                impellerDiaRange = [0, 0]
                # print('------- '+fan['model'] + 'start -----------------')
                # 如果pressureBoundary为最小边界，为true, 如果pressureBoundary为最大边界，为false
                impellerDiaRange[0] = approach_the_boundary(
                    sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[0], True)
                impellerDiaRange[1] = approach_the_boundary(
                    sortFlowRate, impellerDiameter, flowRateData, pressureData, pressureRange[1], False)

                fan['flowRate'] = sortFlowRate

                # impellerDiameterMedian = '{:.0f}'.format(impellerDiameterMedian)

                impellerDiaRange = sorted(impellerDiaRange)
                fan['impellerDiameterRange'] = impellerDiaRange
                # 对存在两段范围符合要求的风机的处理
                an = fit_perf_data(
                    flowRateData, pressureData, impellerDiaRange[0], impellerDiameter)
                x1 = -an[1] / (2 * an[0])
                y1 = x1 * x1 * an[0] + x1 * an[1] + an[2]
                an = fit_perf_data(
                    flowRateData, pressureData, impellerDiaRange[1], impellerDiameter)
                x2 = -an[1] / (2 * an[0])
                y2 = x2 * x2 * an[0] + x2 * an[1] + an[2]
                if (x1 > sortFlowRate and x2 < sortFlowRate):
                    print("选型出现了未考虑到的情况！")
                    pass
                if (x1 < sortFlowRate and x2 > sortFlowRate and (y1 > pressureRange[1] or y2 > pressureRange[1])):

                    impellerD = impellerDiaRange[0]
                    while impellerD < impellerDiaRange[1]:
                        p = fit_perf_data(
                            flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                        if p < pressureRange[0] or p > pressureRange[1]:
                            break
                        impellerD = impellerD + 1
                    # print('impellerD 111')
                    # print(impellerD)
                    tempImpellerDiaRange1 = [impellerDiaRange[0], impellerD]
                    # print('tempImpellerDiaRange')
                    # print(tempImpellerDiaRange1)
                    impellerD = impellerDiaRange[1]
                    while impellerD > impellerDiaRange[0]:
                        p = fit_perf_data(
                            flowRateData, pressureData, impellerD, impellerDiameter, sortFlowRate)
                        if p < pressureRange[0] or p > pressureRange[1]:
                            break
                        impellerD = impellerD - 1
                    # print('impellerD 2222')
                    # print(impellerD)
                    tempImpellerDiaRange2 = [impellerD, impellerDiaRange[1]]
                    # print('tempImpellerDiaRange')
                    # print(tempImpellerDiaRange2)

                    fan['impellerDiameterRange'] = tempImpellerDiaRange1
                    temp = {}
                    for key in fan:
                        temp[key] = fan[key]
                    temp['impellerDiameterRange'] = tempImpellerDiaRange2
                    appendFan.append(temp)

        i = 1
        for item in appendFan:
            # item['model'] = '('+str(i)+')' + item['model']
            item['showModel'] = '(' + str(i) + ')' + item['model']
            item['similarModel'] = '(' + str(i) + ')' + item['model'] + '-' + item['figNum'] + '-' + item['version']
            item['similarId'] = '(' + str(i) + ')' + item['id']
            result.append(item)
            i = i + 1
        # appendFan = []
        req.sortFields = ['pressureDeviation',
                          'impellerDiaDeviation'] + req.sortFields
    delIndex = []
    if req.limitField == 'flowRate':
        for i in range(len(result)):
            fan = result[i]
            if fan['impellerDiameterRange'][0] == fan['impellerDiameterRange'][1]:
                delIndex.append(i)

    # 用户输入的叶轮直径筛选
    if req.impellerDiameterMin and req.impellerDiameterMax:
        for i in range(len(result)):
            fan = result[i]
            if req.limitField == 'flowRate':
                # 存在限定流量、误差字段，变动叶轮尺寸得到压力范围内的原型机
                fan['impellerDiameterRange']
                minNum = max(req.impellerDiameterMin,
                             fan['impellerDiameterRange'][0])
                maxNum = min(req.impellerDiameterMax,
                             fan['impellerDiameterRange'][1])
                if minNum > maxNum:
                    delIndex.append(i)
                    continue
                if req.impellerDiameterMin > fan['impellerDiameterRange'][0]:
                    fan['impellerDiameterRange'][0] = req.impellerDiameterMin
                if req.impellerDiameterMax < fan['impellerDiameterRange'][1]:
                    fan['impellerDiameterRange'][1] = req.impellerDiameterMax
                # if req.impellerDiameterMax > fan['impellerDiameterRange'][0]:
                #     print('-------------------------')
                #     print(req.impellerDiameterMax)
                #     print(fan['impellerDiameterRange'][0])
                #     print('-------------------------')

                #     fan['impellerDiameterRange'] = [
                #         fan['impellerDiameterRange'][0], req.impellerDiameterMax]
                # if req.impellerDiameterMin < fan['impellerDiameterRange'][1]:
                #     fan['impellerDiameterRange'] = [
                #         req.impellerDiameterMin, fan['impellerDiameterRange'][1]]

            elif req.limitField == 'unLimited':

                if not (req.impellerDiameterMin <= fan['impellerDiameter'] and fan[
                    'impellerDiameter'] <= req.impellerDiameterMax):
                    # print('del i')
                    delIndex.append(i)
            i = i + 1
    # 删除超出range的风机
    temp = []
    # print(delIndex)
    for i in range(len(result)):
        if i not in delIndex:
            temp.append(result[i])
    result = temp

    delFan = []
    # 计算需要展示的信息
    if req.limitField == 'flowRate':
        i = 0
        for fan in result:

            perfData = fan['perf']
            impellerDiaRange = fan['impellerDiameterRange']
            impellerDiameter = fan['impellerDiameter']
            # print("impellerDiaRange")
            # print(impellerDiaRange)
            impellerDiaMedian = float('{:.0f}'.format(
                0.5 * (impellerDiaRange[0] + impellerDiaRange[1])))
            fan['impellerDiameterMedian'] = float(impellerDiaMedian)
            if req.impellerDiameterRatioMin and req.impellerDiameterRatioMax:
            # print(impellerDiaRange)
                impellerDiaRangeList = range(impellerDiaRange[0],impellerDiaRange[1]+1)
                impellerDiameterRatioRange = [req.impellerDiameterRatioMin , req.impellerDiameterRatioMax ]
                # 叶轮直径比例修改在这里,计算完之后求交集

                if len(impellerDiameterRatioRange) == 0 :
                    fan['impellerDiameterRange'] = []
                    fan['impellerDiameterMedian'] = None
                    break
                else :
                    # 计算比例对应的直径区间
                    impellerDiameterRatioRange = [math.ceil(req.impellerDiameterRatioMin * impellerDiameter),
                                              math.ceil(req.impellerDiameterRatioMax * impellerDiameter)]
                    impellerDiameterRatioRangeList = range(impellerDiameterRatioRange[0], impellerDiameterRatioRange[1]+1)
                    # print(impellerDiameterRatioRange)
                    # 求交集
                    impellerDiameterRatioRangeList = list(set(impellerDiaRangeList).intersection(set(impellerDiameterRatioRangeList)))
                    # print(impellerDiameterRatioRangeList)
                    impellerDiameterRatioRangeList.sort()
                    # print(impellerDiameterRatioRangeList)

                    if impellerDiameterRatioRangeList == []:
                        impellerDiaRange = []
                        fan['impellerDiameterRange'] = impellerDiaRange
                        fan['impellerDiameterMedian'] = None
                        delFan.append(i)
                        i=i+1
                        continue
                    else:
                        impellerDiaRange = [impellerDiameterRatioRangeList[0] , impellerDiameterRatioRangeList[-1]]
                        fan['impellerDiameterRange'] = impellerDiaRange
                        impellerDiaMedian = float('{:.0f}'.format(0.5 * (impellerDiaRange[0] + impellerDiaRange[1])))
                        fan['impellerDiameterMedian'] = float(impellerDiaMedian)

            if True:
                fR = perfData['flowRate']
                fP = perfData['fullPressure']
                # print('fP')
                # print(fP)
                # 计算相似完的全压
                similarFullPressure = fit_perf_data(
                    fR, fP, impellerDiaMedian, impellerDiameter, sortFlowRate)
                fan['similarFullPressure'] = similarFullPressure
                fan['fullPressure'] = similarFullPressure
                # 计算直径偏差
                impellerDiaDeviation = (
                                               impellerDiaMedian - impellerDiameter) / impellerDiameter
                fan['impellerDiaDeviation'] = float(
                    '{:.2f}'.format(impellerDiaDeviation))

                # elif req.pressureField == 'staticPressure':
                sP = perfData['staticPressure']
                # print('sP')
                # print(sP)
                # 计算相似完的静压
                similarStaticPressure = fit_perf_data(
                    fR, sP, impellerDiaMedian, impellerDiameter, sortFlowRate)

                fan['similarStaticPressure'] = similarStaticPressure
                fan['staticPressure'] = similarStaticPressure
                # 计算全压的偏差
            if req.pressureField == 'fullPressure':
                pressureDeviation = (similarFullPressure - sortPressure) / \
                                    sortPressure * 100
                fan['fullPressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
                # fan['absPressureDeviation'] = abs(fan['fullPressureDeviation'])
                fan['absPressureDeviation'] = fan['fullPressureDeviation']
            # 计算静压的偏差
            elif req.pressureField == 'staticPressure':
                pressureDeviation = (similarStaticPressure - sortPressure) / \
                                    sortPressure * 100
                fan['staticPressureDeviation'] = float(
                    '{:.2f}'.format(pressureDeviation))
                # fan['absPressureDeviation'] = abs(
                #     fan['staticPressureDeviation'])
                fan['absPressureDeviation'] = fan['staticPressureDeviation']
            # req.sortFields.append('absPressureDeviation')
            # if fan['impellerDiameterMedian'] == None or fan['impellerDiameterRange'][0] == [1]:
            #     result.pop(fan)
            # shaftPower计算
            fR = perfData['flowRate']
            sP = perfData['shaftPower']
            #  计算轴功率
            similarShaftPower = fit_perf_data(
                fR, sP, impellerDiaMedian, impellerDiameter, sortFlowRate)
            fan['similarShaftPower'] = similarShaftPower

            fan.pop('perf')
            i = i+1
    result = [fan for num, fan in enumerate(result) if num not in delFan]   #通过枚举删除叶轮直径变化范围为[]的字典
    # 计算排序noise
    i = 0
    for fan in result:
        perfData = await PerfData.get_perf_data_by_model(fan['model'])
        result[i]['noise'] = 0

        # if fan['noise'] is None:
        #     result[i]['noise'] = 0
        i = i + 1

    reverseArr = []
    if len(req.sortFields) != 0:
        for field in req.sortFields:

            if field == 'efficiency':
                reverseArr.append(True)
            if field == 'noise':
                reverseArr.append(False)  # 升序
            if field == 'pressureDeviation':
                reverseArr.append(False)  # 升序
            if field == 'absPressureDeviation':
                reverseArr.append(True)  # 升序
            if field == 'impellerDiaDeviation':
                reverseArr.append(False)  # 升序
    i = 0
    for field in req.sortFields:
        # print(field)

        if len(result) > 0 and field in list(result[0].keys()):
            result = sorted(result, key=lambda e: (
                e.__getitem__(field)), reverse=reverseArr[i])
        i = i + 1
        # if len(req.sortFields) == 2:
    # TODO:双字段排序

    # 分页
    current = int(req.current)
    pageSize = int(req.pageSize)
    total = len(result)
    result = result[
             (current * pageSize - pageSize):
             current * pageSize
             ]
    return resp.ok(data=result, total=total)


'''
name: 
msg: 给定流量 给定压力边界值 求逼近压力边界值的叶轮直径
param {float} sortFlowRate 给定的流量
param {int} impellerDiameter 原型机叶轮直径
param {list} fR 原型机流量实验数据
param {list} fP 原型机压力实验数据
param {float} pressureBoundary 给定的压力边界值
param {bool} returnRignt 返回求出的range的右侧值？如果pressureBoundary为最小边界，为true,如果pressureBoundary为最大边界，为false
return  逼近压力边界值的叶轮直径
'''
def approach_the_boundary(sortFlowRate: float, impellerDiameter: int, fR: list, fP: list, pressureBoundary: float,
                          returnRignt: bool):
    # 取不同叶轮直径 流量 压力 换算

    # 通过给定的流量和原型机叶轮直径估算一个直径范围
    impellerDiaMin = math.ceil(math.pow(
        sortFlowRate / fR[-1], 1 / 3) * impellerDiameter)
    impellerDiaMax = math.ceil(math.pow(
        sortFlowRate / fR[0], 1 / 3) * impellerDiameter)
    # 求最大边界
    i = 0
    impellerDiaRange = [impellerDiaMin, impellerDiaMax]
    # 计算估算出的叶轮直径范围对应的压力范围
    calPressure = [0, 0]
    calPressure[0] = fit_perf_data(
        fR, fP, impellerDiaRange[0], impellerDiameter, sortFlowRate)
    calPressure[1] = fit_perf_data(
        fR, fP, impellerDiaRange[1], impellerDiameter, sortFlowRate)
    # print('calPressure')
    # print(calPressure)
    # i限制了循环次数，
    i = 0 # 最大循环次数，防止死循环
    # 循环结束条件
    while (
            # 范围是否检查完毕
            abs(impellerDiaRange[1] - impellerDiaRange[0]) != 1
           # 压力边界值是否落在计算出来的压力范围内
           or (pressureBoundary - calPressure[0]) * (pressureBoundary - calPressure[1]) > 0)  \
            and i < 20:
        i = i + 1
        # <0
        # 压力边界值是否落在计算出来的压力范围内
        flag1 = ((pressureBoundary - calPressure[0])
                 * (pressureBoundary - calPressure[1])) > 0
        # 如果压力边界值落在计算出来的压力范围外面
        if flag1:
            # 如果压力边界值落在计算出来的压力范围左边
            if (pressureBoundary - calPressure[0]) < 0 and (pressureBoundary - calPressure[1]) < 0:
                # 叶轮区间取的偏右
                # impellerDiaRange[0] = int(
                #     impellerDiaRange[0]/2)if int(impellerDiaRange[0]/2) > impellerDiaMin else impellerDiaMin
                #  叶轮直径区间
                if int(impellerDiaRange[0] / 2) > impellerDiaMin:
                    impellerDiaRange[0] = int(impellerDiaRange[0] / 2)
                else:
                    impellerDiaRange[0] = impellerDiaMin
                    impellerDiaRange[1] = impellerDiaMin
                    break

                # print(impellerDiaRange[0])
            # 如果压力边界值落在计算出来的压力范围右边
            if (pressureBoundary - calPressure[0]) > 0 and (pressureBoundary - calPressure[1]) > 0:
                # 叶轮区间取的偏左
                # print('叶轮区间取的偏左')
                # impellerDiaRange[1] = (
                #     impellerDiaRange[1]+50) if (impellerDiaRange[1]+50) < impellerDiaMax else impellerDiaMax
                if int(impellerDiaRange[1] + 50) < impellerDiaMax:
                    impellerDiaRange[1] = int(impellerDiaRange[1] + 50)
                else:
                    impellerDiaRange[0] = impellerDiaMax
                    impellerDiaRange[1] = impellerDiaMax
                    break
            # 通过修正后的直径区间再次估算压力区间
            calPressure[0] = fit_perf_data(
                fR, fP, impellerDiaRange[0], impellerDiameter, sortFlowRate)
            calPressure[1] = fit_perf_data(
                fR, fP, impellerDiaRange[1], impellerDiameter, sortFlowRate)
            # print('new calPressure')
            # print(calPressure)

            continue
        # 如果压力边界值落在计算出来的压力范围里面
        else:
            medianDia = int(
                (impellerDiaRange[0] + impellerDiaRange[1]) / 2)
            # 计算变形后直径
            # print('medianDia')
            # print(medianDia)
            # 拟合变形后直径对应压力
            mediaPressure = fit_perf_data(
                fR, fP, medianDia, impellerDiameter, sortFlowRate)
            # 如果压力边界值落在计算出来的压力范围的中间值偏左
            if ((pressureBoundary - calPressure[0]) * (pressureBoundary - mediaPressure)) < 0:
                impellerDiaRange[1] = medianDia
                if abs(impellerDiaRange[0] - medianDia) == 1:
                    break
                else:

                    continue
            # 如果压力边界值落在计算出来的压力范围的中间值偏右
            elif ((pressureBoundary - mediaPressure) * (pressureBoundary - calPressure[1])) < 0:
                impellerDiaRange[0] = medianDia
                if abs(impellerDiaRange[1] - medianDia) == 1:
                    break
                else:

                    continue
            else:
                impellerDiaRange[0] = impellerDiaRange[1] = medianDia

                break
    # print(impellerDiaRange)
    if (returnRignt):
        return impellerDiaRange[1]
    else:
        return impellerDiaRange[0]


def approach_the_boundary1(impellerDiaMin: float, impellerDiaMax: float, sortFlowRate: float, impellerDiameter: int,
                           fR: list, fP: list, pressureBoundary: float, returnRignt: bool):
    # 取不同叶轮直径 流量 压力 换算

    # impellerDiaMin = math.ceil(math.pow(
    #     sortFlowRate / fR[-1], 1/3) * impellerDiameter)
    # impellerDiaMax = math.ceil(math.pow(
    #     sortFlowRate / fR[0], 1/3) * impellerDiameter)
    # 求最大边界
    i = 0
    # print('impellerDiaMin')  # 458
    # print(impellerDiaMin)
    # print('impellerDiaMax')  # 737
    # print(impellerDiaMax)
    # print('pressureBoundary')  # 737
    # print(pressureBoundary)
    impellerDiaRange = [impellerDiaMin, impellerDiaMax]
    calPressure = [0, 0]
    # an = fit_perf_data(
    #     fR, fP,  impellerDiaRange[0], impellerDiameter)
    # print('an')
    # print(an)
    # x = -an[1]/(2*an[0])
    # print('x')
    # print(x)
    # y = x*x*an[0]+x*an[1]+an[2]
    # print('y')
    # print(y)
    calPressure[0] = fit_perf_data(
        fR, fP, impellerDiaRange[0], impellerDiameter, sortFlowRate)
    calPressure[1] = fit_perf_data(
        fR, fP, impellerDiaRange[1], impellerDiameter, sortFlowRate)
    # print('calPressure')
    # print(calPressure)
    i = 0
    while (abs(impellerDiaRange[1] - impellerDiaRange[0]) != 1 or
           (pressureBoundary - calPressure[0]) * (pressureBoundary - calPressure[1]) > 0) and i < 20:

        i = i + 1
        print('---------' + str(i) + '-----------------')
        print(impellerDiaRange)
        # <0
        flag1 = ((pressureBoundary - calPressure[0])
                 * (pressureBoundary - calPressure[1])) > 0
        # print('flag1')
        # print(flag1)
        # print('(pressureBoundary - calPressure[0])')
        # print((pressureBoundary - calPressure[0]))
        # print('(pressureBoundary - calPressure[1])')
        # print((pressureBoundary - calPressure[1]))
        if flag1:

            if (pressureBoundary - calPressure[0]) < 0 and (pressureBoundary - calPressure[1]) < 0:
                # if (pressureBoundary)
                # 叶轮区间取的偏右
                # print('叶轮区间取的偏右')
                # impellerDiaRange[0] = int(
                #     impellerDiaRange[0]/2)if int(impellerDiaRange[0]/2) > impellerDiaMin else impellerDiaMin
                if int(impellerDiaRange[0] / 2) > impellerDiaMin:
                    impellerDiaRange[0] = int(impellerDiaRange[0] / 2)
                else:
                    impellerDiaRange[0] = impellerDiaMin
                    impellerDiaRange[1] = impellerDiaMin
                    break

                # print(impellerDiaRange[0])
            if (pressureBoundary - calPressure[0]) > 0 and (pressureBoundary - calPressure[1]) > 0:
                # 叶轮区间取的偏左
                # print('叶轮区间取的偏左')
                # impellerDiaRange[1] = (
                #     impellerDiaRange[1]+50) if (impellerDiaRange[1]+50) < impellerDiaMax else impellerDiaMax
                if int(impellerDiaRange[1] + 50) < impellerDiaMax:
                    impellerDiaRange[1] = int(impellerDiaRange[1] + 50)
                else:
                    impellerDiaRange[0] = impellerDiaMax
                    impellerDiaRange[1] = impellerDiaMax
                    break

            # print(impellerDiaRange)
            # an = fit_perf_data(
            #     fR, fP,  impellerDiaRange[0], impellerDiameter)
            # x = -an[1]/(2*an[0])
            # print('impellerDiaRange[0]')
            # print(impellerDiaRange[0])
            # print('x')
            # print(x)
            # y = x*x*an[0]+x*an[1]+an[2]
            # print('y')
            # print(y)

            calPressure[0] = fit_perf_data(
                fR, fP, impellerDiaRange[0], impellerDiameter, sortFlowRate)
            calPressure[1] = fit_perf_data(
                fR, fP, impellerDiaRange[1], impellerDiameter, sortFlowRate)
            # print('new calPressure')
            # print(calPressure)

            continue
        else:
            medianDia = int(
                (impellerDiaRange[0] + impellerDiaRange[1]) / 2)
            # print('medianDia')
            # print(medianDia)

            mediaPressure = fit_perf_data(
                fR, fP, medianDia, impellerDiameter, sortFlowRate)
            # print('mediaPressure')
            # print(mediaPressure)
            # print('(pressureBoundary - calPressure[0])')
            # print((pressureBoundary - calPressure[0]))
            # print('(pressureBoundary - mediaPressure)')
            # print((pressureBoundary - mediaPressure))
            # print('(pressureBoundary - calPressure[1])')
            # print((pressureBoundary - calPressure[1]))
            if ((pressureBoundary - calPressure[0]) * (pressureBoundary - mediaPressure)) < 0:
                impellerDiaRange[1] = medianDia
                if abs(impellerDiaRange[0] - medianDia) == 1:
                    break
                else:

                    continue
            elif ((pressureBoundary - mediaPressure) * (pressureBoundary - calPressure[1])) < 0:
                impellerDiaRange[0] = medianDia
                if abs(impellerDiaRange[1] - medianDia) == 1:
                    break
                else:

                    continue
            else:
                impellerDiaRange[0] = impellerDiaRange[1] = medianDia

                break
    # print('!!!!impellerDiaRange')
    # print(impellerDiaRange)
    if (returnRignt):
        return impellerDiaRange[1]
    else:
        return impellerDiaRange[0]


def get_path(model, fileName=None):
    model = validateStr(model)
    if (fileName is None):
        return '/psad/fan/' + model
    filePath = '/psad/fan/' + model + '/' + fileName

    return filePath


async def save_file(filePath, file):
    dir = '/'.join(filePath.split('/')[:-1])
    name = filePath.split('/')[-1]
    # print('dir')
    # print(dir)
    # print('name')
    # print(name)
    # print(os.path.exists(dir))
    try:
        if not os.path.exists(dir):
            os.makedirs(dir)
        for f in os.listdir(dir):
            # 同名但文件类型不同的文件需删除
            if file.filename.split('.')[-1] != 'dwg':
                temp = f.split('.')
                fname = '.'.join(temp[:-1])
                ftype = temp[-1]
                temp = name.split('.')
                sname = '.'.join(temp[:-1])
                stype = temp[-1]
                if (f.split('.')[-1] != 'dwg' and fname == sname and ftype != stype):
                    os.remove(dir + '/' + f)
                print('same name')
        print('filePath')
        print(filePath)
        res = await file.read()
        with open(filePath, "wb") as f:
            f.write(res)
        return True

    except Exception as e:
        # return False
        return resp.fail(resp.DataStoreFail.set_msg('文件存储失败' + str(e)), detail=str(e))


# ,
@router.post("/add", summary="添加风机", name="添加风机", dependencies=[Depends(get_db)], include_in_schema=False)
async def add_fan(
        applicationModelId: str = Form(None),  # TODO:None=>... required字段
        applicationModel: str = Form(None),
        # categoryId: str = Form(None),
        category: List[str] = Form(None),
        model: str = Form(None),
        coolObject: str = Form(None),

        figNum: str = Form(None),
        version: str = Form(None),
        flowRate: float = Form(None),
        shaftPower: float = Form(None),
        efficiency: float = Form(None),

        fullPressure: float = Form(None),
        staticPressure: float = Form(None),

        impellerDiameter: float = Form(None),
        weight: float = Form(None),

        motorModel: str = Form(None),
        powerFrequency: float = Form(None),
        motorPower: float = Form(None),
        motorSpeedMin: float = Form(None),
        motorSpeed: float = Form(None),

        ratedVoltage: str = Form(None),
        ratedCurrent: float = Form(None),

        impellerOuterDiameter: float = Form(None),
        impellerInnerDiameter: float = Form(None),
        impellerOutlet: float = Form(None),
        impellerInlet: float = Form(None),
        exitCorner: float = Form(None),
        inletCorner: float = Form(None),
        impellerNumber: int = Form(None),

        remark1: str = Form(None),
        remark2: str = Form(None),
        sampleDesc: str = Form(None),
        status: str = Form(None),
        altitude: str = Form(None),
        temperature: str = Form(None),
        humidity: str = Form(None),
        createBy: str = Form(None),

        #    perfData: sys_fan_schema.CreatePerfData = Form(None),
        perfData: str = Form(None),
        # img3d: List[UploadFile] = File(None),
        # aerodynamicSketch: List[UploadFile] = File(None),
        # outlineFile: List[UploadFile] = File(None),
        # labReport: List[UploadFile] = File(None),
        # designSpecification: List[UploadFile] = File(None),
        img3d: List[Union[UploadFile, str]] = File(None),
        aerodynamicSketch: List[Union[UploadFile, str]] = File(None),
        outlineFile: List[Union[UploadFile, str]] = File(None),
        labReport: List[Union[UploadFile, str]] = File(None),
        designSpecification: List[Union[UploadFile, str]] = File(None),
        #     List[Union[UploadFile,str]]
        # perfData: sys_fan_schema.FanAdd,  # 前端parameters传递参数 修改比较麻烦
) -> Any:
    """
    params perfData :性能曲线数据转excel存储信息
    - header : 表头,
    - dataIndex : data的key,可用于过滤导出数据
    - data : 性能曲线数据\n

        perfData:{
             header:['header'],
             dataIndex:['key'],
             data:[{'key':'value}]}
    """
    imgDict = {
        # '三维图': img3d,
        'img3d': img3d,
        # 'imgOutline': imgOutline,
        # 'technicalFile': technicalFile
    }
    pathList = {
        'img3d': []}

    # 文件存储路径：/psad/fan/model/model+figNum+version+fileName+number.fileType

    fileDict = {
        'img3d': img3d,
        'outlineFile': outlineFile,
        'labReport': labReport,
        'designSpecification': designSpecification,
        'aerodynamicSketch': aerodynamicSketch,
    }

    # -------------------------------------
    perfData = perfData.replace('null', '')
    perfData = eval(perfData)
    # # excel存入
    # sheetData = []
    # for data in perfData['data']:
    #     temp = []
    #     for item in perfData['dataIndex']:
    #         if item not in data.keys():
    #             pass
    #         else:
    #             temp.append(data[item])
    #     sheetData.append(temp)
    #
    # # print('sheetData')
    # # print(sheetData)
    # sheetName = model+'-'+figNum+'-'+version+'-perf.xls'
    # sheetPath = get_path(model, sheetName)
    # # print('sheetPath:'+sheetPath)
    #
    # write_excel_xls(sheetPath, sheetName, perfData['header'], sheetData)
    # pathList['perfExcel'] = sheetPath
    #
    # 性能曲线数据
    perfData = perfData['data']
    # 按flowRate升序排列
    perfData = sorted(perfData, key=lambda e: e.__getitem__(
        'flowRate'), reverse=False)
    # -------------------------------------

    print('category')
    print(category)
    # temp =await FanCategory.select_id_by_series_and_name(category[0],category[1])
    temp = await async_db.execute(FanCategory.select().where(
        FanCategory.parentId == category[0], FanCategory.id == category[1]))
    temp = list(temp)
    print('temp')
    print(temp)
    temp = temp[0]
    temp = model_to_dict(temp)

    seriesId = int(temp['id'])
    print('seriesId')
    print(seriesId)
    time = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')

    fan = {
        'applicationModelId': applicationModelId,
        'applicationModel': applicationModel,
        'coolObject': coolObject,
        'seriesId': seriesId,
        # 'category': category[1],
        'id': uuid.uuid1(),
        'model': model,
        'figNum': figNum,
        'version': version,

        'flowRate': flowRate,

        'fullPressure': fullPressure,
        'staticPressure': staticPressure,

        'shaftPower': shaftPower,
        'efficiency': efficiency,

        'motorModel': motorModel,
        'powerFrequency': powerFrequency,

        'motorPower': motorPower,

        'motorSpeedMin': motorSpeedMin,
        'motorSpeed': motorSpeed,

        'ratedVoltage': ratedVoltage,
        'ratedCurrent': ratedCurrent,

        'impellerDiameter': impellerDiameter,
        'weight': weight,

        'impellerOuterDiameter': impellerOuterDiameter,
        'impellerInnerDiameter': impellerInnerDiameter,
        'impellerOutlet': impellerOutlet,
        'impellerInlet': impellerInlet,
        'exitCorner': exitCorner,
        'inletCorner': inletCorner,
        'impellerNumber': impellerNumber,

        'altitude': altitude,
        'temperature': temperature,
        'humidity': humidity,
        'remark1': remark1,
        'remark2': remark2,
        "sampleDesc": sampleDesc,
        'status': status,
        # 'outlineFile' : pathList['outlineFile'],
        'img3d': pathList['img3d'],
        # 'perfExcel': pathList['perfExcel'],
        # TODO:
        'createAt': time,
        'updateAt': time,
        'createBy': createBy,
        'updateBy': createBy,
    }
    try:
        # if True:
        async with db.atomic_async():
            # result =await Fan.add_fan_by_dict(fan)
            # 在主表/正式表中检查主键是否存在
            # 检查是否与主表“风机型号-图号-版本号”主键是否重复
            fanList = await async_db.execute(
                Fan.select().where(Fan.model == model, Fan.figNum == figNum,
                                   Fan.version == version).dicts())
            fanList = list(fanList)
            if len(fanList) >= 1:
                return resp.fail(resp.DataStoreFail.set_msg('该风机型号-图号-版本号已存在！'))
            fanId = await FanUpdateRecord.add_fan_by_dict(fan)
            # await AuditRecord.add_audit_record({
            #     'auditBizId': fanId,
            #     'userId': createBy,
            #     'auditType': 'fanAddAudit',
            # })
            for item in perfData:
                item['modelId'] = model
                item['fanId'] = fanId
                # item.pop('key')
                if 'index' in item.keys():
                    item.pop('index')
            await PerfData.add_perf_datas(perfData)

            fileNamePrefix = get_save_bizeId(model, figNum, version)
            bizId = fanId
            # 删除原有文件记录
            await FileInfo.delete_by_biz_id(bizId)
            res = await async_db.execute(
                FileInfo.select(
                    fn.group_concat(FileInfo.fileName).python_value(convert_arr).alias('name')).group_by(
                    FileInfo.bizId).where(
                    FileInfo.bizId == bizId).dicts())
            res = list(res)
            if len(res) == 0:
                nameList = []
            else:
                nameList = res[0]['name']
            # for fileId in imgDict:
            #     if (imgDict[fileId] != None):
            #         imgList = imgDict[fileId]
            #         # result = await up_file(bizId, fileId,fileNamePrefix, imgList)
            #         i = 1
            #         for img in imgList:
            #             if type(img) == str:
            #                 fileInfo = json.loads(img)
            #                 while fileNamePrefix + '-' + fileId + '-' + str(i) + '.' + fileInfo['fileType'] in nameList:
            #                     i = i + 1
            #                 fileInfo['bizId'] = bizId
            #                 fileInfo['createAt'] = datetime.strftime(
            #                     datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
            #                 # fileInfo['updateAt'] = fileInfo['createAt']
            #                 fileInfo['fileName'] = fileNamePrefix + '-' + fileInfo['bizType'] + '-' + str(i) + '.' + \
            #                                        fileInfo['fileType']
            #                 fileInfo['id'] = uuid.uuid1()
            #                 await FileInfo.add(fileInfo)
            #             # 获取文件
            #             else:
            #                 result = await up_file(bizId, fileId, fileNamePrefix, [img])
            for fileId in fileDict:
                if (fileDict[fileId] != None):
                    fileList = fileDict[fileId]
                    i = 1
                    for file in fileList:
                        if type(file) == str:
                            fileInfo = json.loads(file)
                            if 'bizId' not in fileInfo:
                                await save_file_info(fileInfo, bizId, fileId, fileNamePrefix)
                            else:
                                fileInfo = json.loads(file)
                                while fileNamePrefix + '-' + fileInfo['bizType'] + '-' + str(i) + '.' + fileInfo[
                                    'fileType'] in nameList:
                                    i = i + 1
                                fileInfo['bizId'] = bizId
                                fileInfo['createAt'] = datetime.strftime(
                                    datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
                                # fileInfo['updateAt'] = fileInfo['createAt']
                                fileInfo['fileName'] = fileNamePrefix + '-' + fileNameDict[fileInfo['bizType']] + '-' + str(i) + '.' + \
                                                       fileInfo['fileType']
                                fileInfo['id'] = uuid.uuid1()
                                await FileInfo.add(fileInfo)
                        # 获取文件
                        else:
                            result = await up_file(bizId, fileId, fileNamePrefix, [file])


    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('该风机型号-图号-版本号已存在！'), detail=str(e))

    except Exception as e:

        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok()


@router.post("/addPerfData", summary="添加风机实验数据,只有某些字段接受修改", name="添加风机实验数据",
             dependencies=[Depends(get_db)], include_in_schema=False)
async def add_fan_perf_data(
        model: str = Form(...),
        figNum: str = Form(...),
        version: str = Form(...),
        perfData: str = Form(None),
        # img3d: List[UploadFile] = File(None),
        # aerodynamicSketch: List[UploadFile] = File(None),
        # outlineFile: List[UploadFile] = File(None),
        # labReport: List[UploadFile] = File(None),
        # designSpecification: List[UploadFile] = File(None),
        img3d: List[Union[UploadFile, str]] = File(None),
        aerodynamicSketch: List[Union[UploadFile, str]] = File(None),
        outlineFile: List[Union[UploadFile, str]] = File(None),
        labReport: List[Union[UploadFile, str]] = File(None),
        designSpecification: List[Union[UploadFile, str]] = File(None),
        copyId: str = Form(...),
        status: str = Form(...),
        userInfo: Userinfo = Depends(deps.get_current_userinfo),

) -> Any:
    """
    params perfData :性能曲线数据转excel存储信息
    - header : 表头,
    - dataIndex : data的key,可用于过滤导出数据
    - data : 性能曲线数据\n

        perfData:{
             header:['header'],
             dataIndex:['key'],
             data:[{'key':'value}]}
    """
    imgDict = {
        # '三维图': img3d,
        'img3d': img3d,
        # 'imgOutline': imgOutline,
        # 'technicalFile': technicalFile
    }
    # 文件存储路径：/psad/fan/model/model+figNum+version+fileName+number.fileType

    fileDict = {
        'img3d': img3d,
        'outlineFile': outlineFile,
        'labReport': labReport,
        'designSpecification': designSpecification,
        'aerodynamicSketch': aerodynamicSketch,
    }

    # -------------------------------------
    perfData = perfData.replace('null', '')
    perfData = eval(perfData)
    # # excel存入
    # sheetData = []
    # for data in perfData['data']:
    #     temp = []
    #     for item in perfData['dataIndex']:
    #         if item not in data.keys():
    #             pass
    #         else:
    #             temp.append(data[item])
    #     sheetData.append(temp)
    #
    # # print('sheetData')
    # # print(sheetData)
    # sheetName = model+'-'+figNum+'-'+version+'-perf.xls'
    # sheetPath = get_path(model, sheetName)
    # # print('sheetPath:'+sheetPath)
    #
    # write_excel_xls(sheetPath, sheetName, perfData['header'], sheetData)
    # pathList['perfExcel'] = sheetPath
    #
    # 性能曲线数据
    perfData = perfData['data']
    # 按flowRate升序排列
    perfData = sorted(perfData, key=lambda e: e.__getitem__(
        'flowRate'), reverse=False)
    # -------------------------------------
    # temp =await FanCategory.select_id_by_series_and_name(category[0],category[1])
    # temp = await async_db.execute(FanCategory.select().where(
    #     FanCategory.parentId==category[0],FanCategory.id==category[1]))
    # temp=list(temp)
    # print('temp')
    # print(temp)
    # temp = temp[0]
    # temp = model_to_dict(temp)
    #
    # seriesId= int(temp['id'])

    time = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    fan = await Fan.single_by_id(copyId)
    fan['id'] = str(uuid.uuid1())
    fan['model'] = model
    fan['figNum'] = figNum
    fan['version'] = version
    fan['status'] = status
    fan['createAt'] = time
    fan['updateAt'] = time
    fan['createBy'] = userInfo['account']
    fan['updateBy'] = userInfo['account']
    try:
        # if True:
        async with db.atomic_async():
            # result =await Fan.add_fan_by_dict(fan)
            # TODO:在主表/正式表中检查主键是否存在
            # 检查是否与主表“风机型号-图号-版本号”主键是否重复
            fanList = await async_db.execute(
                Fan.select().where(Fan.model == fan['model'], Fan.figNum == fan['figNum'],
                                   Fan.version == fan['version']).dicts())
            fanList = list(fanList)
            if len(fanList) > 0:
                return resp.fail(resp.DataStoreFail.set_msg('该风机型号-图号-版本号已存在！'))
            result = await FanUpdateRecord.add_fan_by_dict(fan)

            version1 = await async_db.execute(
                FanUpdateRecord.select().where(
                    FanUpdateRecord.model == fan['model'],
                    FanUpdateRecord.figNum == fan['figNum'],
                    FanUpdateRecord.version == fan['version'],
                ).dicts())
            version1 = len(list(version1))
            await FanUpdateRecordRelp.add(
                {'id': fan['id'], 'type': 'copy', 'version': version1, 'fanId': fan['id'], 'copyId': copyId})
            for item in perfData:
                item['modelId'] = model
                item['fanId'] = result
                # item.pop('key')
                if 'index' in item.keys():
                    item.pop('index')
            await PerfData.add_perf_datas(perfData)
            fileNamePrefix = get_save_bizeId(model, figNum, version)
            bizId = result
            # 删除原有文件记录
            await FileInfo.delete_by_biz_id(bizId)
            # 获取文件命名序号
            # res = await async_db.execute(
            #     FileInfo.select(
            #         fn.group_concat(FileInfo.fileName).python_value(convert_arr).alias('name')).group_by(
            #         FileInfo.bizId).where(
            #         FileInfo.bizId == bizId).dicts())
            # res = list(res)
            # if len(res) == 0:
            #     nameList = []
            # else:
            #     nameList = res[0]['name']
            # 获取文件命名序号
            # for fileId in imgDict:
            #     if imgDict[fileId] != None:
            #         imgList = imgDict[fileId]
            #         for img in imgList:
            #             if type(img) == str:
            #                 fileInfo = json.loads(img)
            #                 patt = r'\-\d{1,}\.'
            #                 pattern = re.compile(patt)
            #                 result = pattern.findall(fileInfo['fileName'])
            #                 # -i.
            #                 i = result[-1]
            #                 fileInfo['bizId'] = bizId
            #                 fileInfo['createAt'] = datetime.strftime(
            #                     datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
            #                 # fileInfo['updateAt'] = fileInfo['createAt']
            #                 fileInfo['fileName'] = fileNamePrefix + '-' + fileInfo['bizType'] + i + fileInfo['fileType']
            #                 fileInfo['id'] = str(uuid.uuid1())
            #                 await FileInfo.add(fileInfo)
            #         for img in imgList:
            #             if type(img) != str:
            #                 # 获取文件
            #                 # else:
            #                 await up_file(bizId, fileId, fileNamePrefix, [img])

            for fileId in fileDict:
                if fileDict[fileId] is not None:
                    fileList = fileDict[fileId]
                    for file in fileList:
                        if type(file) == str:
                            fileInfo = json.loads(file)
                            # 新增实验数据新上传的文件
                            if 'bizId' not in fileInfo:
                                await save_file_info(fileInfo, bizId, fileId, fileNamePrefix)
                            else:
                                patt = r'\-\d{1,}\.'
                                pattern = re.compile(patt)
                                result = pattern.findall(fileInfo['fileName'])
                                # -i.
                                i = result[-1]
                                fileInfo['bizId'] = bizId
                                fileInfo['createAt'] = datetime.strftime(
                                    datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
                                # fileInfo['updateAt'] = fileInfo['createAt']
                                fileInfo['fileName'] = fileNamePrefix + '-' + fileNameDict[fileInfo['bizType']]+ i + fileInfo['fileType']
                                fileInfo['id'] = str(uuid.uuid1())
                                await FileInfo.add(fileInfo)
                    for file in fileList:
                        if type(file) != str:
                            # 获取文件
                            await up_file(bizId, fileId, fileNamePrefix, [file])
    except IntegrityError as e:
        return resp.fail(resp.DataStoreFail.set_msg('该风机型号-图号-版本号已存在！'), detail=str(e))
    except Exception as e:
        return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok()


@router.post("/update", summary="更新风机信息", name="更新风机信息", dependencies=[Depends(get_db)], deprecated=True,
             include_in_schema=False)
async def update_fan(applicationModelId: str = Form(None),  # TODO:None=>... required字段
                     applicationModel: str = Form(None),
                     # categoryId: str = Form(None),
                     category: List[str] = Form(None),
                     id: str = Form(None),
                     model: str = Form(None),
                     coolObject: str = Form(None),

                     figNum: str = Form(None),
                     version: str = Form(None),
                     flowRate: float = Form(None),
                     shaftPower: float = Form(None),
                     efficiency: float = Form(None),

                     fullPressure: float = Form(None),
                     staticPressure: float = Form(None),

                     impellerDiameter: float = Form(None),
                     weight: float = Form(None),

                     motorModel: str = Form(None),
                     powerFrequency: float = Form(None),
                     motorPower: float = Form(None),
                     motorSpeedMin: float = Form(None),
                     motorSpeed: float = Form(None),

                     ratedVoltage: str = Form(None),
                     ratedCurrent: float = Form(None),

                     remark1: str = Form(None),
                     remark2: str = Form(None),
                     sampleDesc: str = Form(None),

                     altitude: str = Form(None),
                     temperature: str = Form(None),
                     humidity: str = Form(None),
                     updateBy: str = Form(None),

                     perfData: str = Form(None),
                     img3d: List[Union[UploadFile, str]] = File(None),
                     aerodynamicSketch: List[Union[UploadFile, str]] = File(None),
                     outlineFile: List[Union[UploadFile, str]] = File(None),
                     labReport: List[Union[UploadFile, str]] = File(None),
                     designSpecification: List[Union[UploadFile, str]] = File(None),
                     status: str = Form(None),
                     ) -> Any:
    """
    params perfData :性能曲线数据转excel存储信息
    - header : 表头,
    - dataIndex : data的key,可用于过滤导出数据
    - data : 性能曲线数据\n

        perfData:{
             header:['header'],
             dataIndex:['key'],
             data:[{'key':'value}]}
    """

    imgDict = {
        # '三维图': img3d,
        'img3d': img3d,
        # 'imgOutline': imgOutline,
        # 'technicalFile': technicalFile
    }

    # 文件存储路径：/psad/fan/model/model+figNum+version+fileName+number.fileType

    fileDict = {
        'img3d': img3d,
        'outlineFile': outlineFile,
        'labReport': labReport,
        'designSpecification': designSpecification,
        'aerodynamicSketch': aerodynamicSketch,
    }

    perfData = perfData.replace('null', '')

    perfData = eval(perfData)
    # excel存入
    # sheetData = []
    # for data in perfData['data']:
    #     temp = []
    #     for item in perfData['dataIndex']:
    #         if item not in data.keys():
    #             pass
    #         else:
    #             temp.append(data[item])
    #     sheetData.append(temp)
    #
    # # print('sheetData')
    # # print(sheetData)
    # sheetName = model+'-perf.xls'
    # sheetPath = get_path(model, sheetName)
    # # print('sheetPath:'+sheetPath)
    #
    # write_excel_xls(sheetPath, sheetName, perfData['header'], sheetData)
    # pathList['perfExcel'] = sheetPath

    # 性能曲线数据
    perfData = perfData['data']

    # 按flowRate升序排列
    perfData = sorted(perfData, key=lambda e: e.__getitem__(
        'flowRate'), reverse=False)

    for item in perfData:
        item['modelId'] = model
        item['fanId'] = id
        if id in item.keys():
            item.pop('id')
        # item.pop('key')
        # if 'index' in item.keys():
        #     # 修改过的数据记录会多一个index字段
        #     item.pop('index')
        # if 'title' in item.keys():
        #     # 手动新增的数据记录会多一个index字段
        #     item.pop('index')
    temp = await async_db.execute(FanCategory.select().where(
        FanCategory.parentId == category[0], FanCategory.id == category[1]))
    temp = list(temp)
    print('temp')
    print(temp)
    temp = temp[0]
    temp = model_to_dict(temp)
    # temp = await FanCategory.select_id_by_series_and_name(category)
    # temp = model_to_dict(temp)

    seriesId = int(temp['id'])
    time = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    fan = {
        'applicationModelId': applicationModelId,
        'applicationModel': applicationModel,
        'coolObject': coolObject,
        'seriesId': seriesId,
        # 'category': category[1],

        'id': id,
        'model': model,
        'figNum': figNum,
        'version': version,

        'flowRate': flowRate,

        'fullPressure': fullPressure,
        'staticPressure': staticPressure,

        'shaftPower': shaftPower,
        'efficiency': efficiency,

        'motorModel': motorModel,
        'powerFrequency': powerFrequency,

        'motorPower': motorPower,

        'motorSpeedMin': motorSpeedMin,
        'motorSpeed': motorSpeed,

        'ratedVoltage': ratedVoltage,
        'ratedCurrent': ratedCurrent,

        'impellerDiameter': impellerDiameter,
        'weight': weight,

        'altitude': altitude,
        'temperature': temperature,
        'humidity': humidity,
        'remark1': remark1,
        'remark2': remark2,
        'sampleDesc': sampleDesc,
        # 'outlineFile' : pathList['outlineFile'],
        # 'img3d': pathList['img3d'],
        # 'perfExcel': pathList['perfExcel'],
        'updateAt': datetime.strftime(datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S'),
        'updateBy': updateBy,
        'status': status
    }
    # fan = dict_to_model(Fan, fan)
    fan = dict_to_model(FanUpdateRecord, fan)
    try:
        # if True:
        async with db.atomic_async():
            bizId = id
            fileNamePrefix = get_save_bizeId(model, figNum, version)
            # fileInfo表先删再增
            await FileInfo.delete_by_biz_id(bizId)
            # for fileId in imgDict:
            #     if imgDict[fileId] is not None:
            #         imgList = imgDict[fileId]
            #         for img in imgList:
            #             if type(img) == str:
            #                 print('img str')
            #                 print(img)
            #                 # img = img.replace('null','')
            #                 # fileInfo = ast.literal_eval(img)
            #                 fileInfo = json.loads(img)
            #                 await FileInfo.add(fileInfo)
            #             else:
            #                 print(img)
            #                 result = await up_file(bizId, fileId, fileNamePrefix, [img])

            for fileId in fileDict:
                if fileDict[fileId] is not None:
                    fileList = fileDict[fileId]
                    for file in fileList:
                        if type(file) == str:
                            fileInfo = json.loads(file)
                            print('file str')
                            print(file)
                            # img = img.replace('null','')
                            # fileInfo = ast.literal_eval(img)
                            if 'bizId' not in fileInfo:
                                await save_file_info(fileInfo, bizId, fileId, fileNamePrefix)
                            else:
                                patt = r'\-\d{1,}\.'
                                pattern = re.compile(patt)
                                result = pattern.findall(fileInfo['fileName'])
                                # -i.
                                i = result[-1]
                                # while fileNamePrefix + '-' + fileNameDict[fileId] + '-' + str(i) + '.' + fileInfo[
                                #     'fileType'] in nameList:
                                #     i = i + 1
                                fileInfo['bizType'] = fileId
                                fileInfo['fileName'] = fileNamePrefix + '-' + fileNameDict[fileId] + i + fileInfo[
                                    'fileType']
                                await FileInfo.add(fileInfo)
                    for file in fileList:
                        if type(file) != str:
                            await up_file(bizId, fileId, fileNamePrefix, [file])
                # raise HTTPException(400, '文件存储失败，详情：' )
            # perfData 先删再增
            await PerfData.del_perf_data([id])
            await PerfData.add_perf_datas(perfData)
            # result =await Fan.update_fan(fan)
            result = await FanUpdateRecord.update_fan(fan)

            return resp.ok()
    except Exception as e:
        print('e')
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))


@router.post("/alter", summary="变更风机信息", name="变更风机信息", dependencies=[Depends(get_db)], deprecated=True,
             include_in_schema=False)
async def alter_fan(applicationModelId: str = Form(None),  # TODO:None=>... required字段
                    applicationModel: str = Form(None),
                    # categoryId: str = Form(None),
                    category: List[str] = Form(None),
                    id: str = Form(None),
                    model: str = Form(None),
                    coolObject: str = Form(None),

                    figNum: str = Form(None),
                    version: str = Form(None),
                    flowRate: float = Form(None),
                    shaftPower: float = Form(None),
                    efficiency: float = Form(None),

                    fullPressure: float = Form(None),
                    staticPressure: float = Form(None),

                    impellerDiameter: float = Form(None),
                    weight: float = Form(None),

                    motorModel: str = Form(None),
                    powerFrequency: float = Form(None),
                    motorPower: float = Form(None),
                    motorSpeedMin: float = Form(None),
                    motorSpeed: float = Form(None),

                    ratedVoltage: str = Form(None),
                    ratedCurrent: float = Form(None),

                    impellerOuterDiameter: float = Form(None),
                    impellerInnerDiameter: float = Form(None),


                    impellerOutlet: float = Form(None),
                    impellerInlet: float = Form(None),
                    exitCorner: float = Form(None),
                    inletCorner: float = Form(None),
                    impellerNumber: int = Form(None),
                    remark1: str = Form(None),
                    remark2: str = Form(None),
                    sampleDesc: str = Form(None),

                    altitude: str = Form(None),
                    temperature: str = Form(None),
                    humidity: str = Form(None),
                    updateBy: str = Form(None),

                    perfData: str = Form(None),
                    img3d: List[Union[UploadFile, str]] = File(None),
                    aerodynamicSketch: List[Union[UploadFile, str]] = File(None),
                    outlineFile: List[Union[UploadFile, str]] = File(None),
                    labReport: List[Union[UploadFile, str]] = File(None),
                    designSpecification: List[Union[UploadFile, str]] = File(None),
                    # status: str = Form(None),
                    # alterId: str = Form(None),
                    reason: str = Form(None),
                    ) -> Any:
    """
    params perfData :性能曲线数据转excel存储信息
    - header : 表头,
    - dataIndex : data的key,可用于过滤导出数据
    - data : 性能曲线数据\n

        perfData:{
             header:['header'],
             dataIndex:['key'],
             data:[{'key':'value}]}
    """
    # print('id')
    # print(id)
    recordFanId = str(uuid.uuid1())
    alterIdResult = await FanUpdateRecordRelp.query_by_id(id)
    alterId = alterIdResult['fanId']
    # --是否存在未审核的变更--
    alterRecord = await FanUpdateRecord.single_by_id(alterId)
    unAlterRecord = await async_db.execute(FanUpdateRecord.select().where(
        FanUpdateRecord.model == alterRecord['model'],
        FanUpdateRecord.figNum == alterRecord['figNum'],
        FanUpdateRecord.version == alterRecord['version'],
        FanUpdateRecord.status.in_(['auditAlter', 'auditByLead']),
    ).dicts())
    unAlterRecord = list(unAlterRecord)
    if len(unAlterRecord) > 0:
        return resp.fail(resp.Unauthorized.set_msg('存在未审核的记录！'))
    # --是否存在未审核的变更--

    # 文件存储路径：/psad/fan/model/model+figNum+version+fileName+number.fileType
    fileDict = {
        'img3d': img3d,
        'outlineFile': outlineFile,
        'labReport': labReport,
        'designSpecification': designSpecification,
        'aerodynamicSketch': aerodynamicSketch,
    }

    perfData = perfData.replace('null', '')
    perfData = eval(perfData)
    # 性能曲线数据
    perfData = perfData['data']

    # 按flowRate升序排列
    perfData = sorted(perfData, key=lambda e: e.__getitem__(
        'flowRate'), reverse=False)

    for item in perfData:
        item['modelId'] = model
        item['fanId'] = recordFanId
        if 'id' in item.keys():
            item.pop('id')
    temp = await async_db.execute(FanCategory.select().where(
        FanCategory.parentId == category[0], FanCategory.id == category[1]))
    temp = list(temp)
    temp = temp[0]
    temp = model_to_dict(temp)
    seriesId = int(temp['id'])

    time = datetime.strftime(
        datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
    alterFan = await FanUpdateRecord.single_by_id(id)
    # 要变更的风机信息的原记录alterFan
    # 以下只允许改变型号图号版本号以外的字段
    fan = {
        'applicationModelId': applicationModelId,
        'applicationModel': applicationModel,
        'coolObject': coolObject,
        'seriesId': seriesId,
        # 'category': category[1],

        'id': recordFanId,
        'model': alterFan['model'],
        'figNum': alterFan['figNum'],
        'version': alterFan['version'],

        'flowRate': flowRate,

        'fullPressure': fullPressure,
        'staticPressure': staticPressure,

        'shaftPower': shaftPower,
        'efficiency': efficiency,

        'motorModel': motorModel,
        'powerFrequency': powerFrequency,

        'motorPower': motorPower,

        'motorSpeedMin': motorSpeedMin,
        'motorSpeed': motorSpeed,

        'ratedVoltage': ratedVoltage,
        'ratedCurrent': ratedCurrent,

        'impellerDiameter': impellerDiameter,
        'weight': weight,

        'altitude': altitude,
        'temperature': temperature,
        'humidity': humidity,

        'impellerOuterDiameter': impellerOuterDiameter,
        'impellerInnerDiameter': impellerInnerDiameter,
        'impellerOutlet': impellerOutlet,
        'impellerInlet': impellerInlet,
        'exitCorner': exitCorner,
        'inletCorner': inletCorner,
        'impellerNumber': impellerNumber,

        'remark1': remark1,
        'remark2': remark2,
        'sampleDesc': sampleDesc,
        # 'outlineFile' : pathList['outlineFile'],
        # 'img3d': pathList['img3d'],
        # 'perfExcel': pathList['perfExcel'],

        'updateAt': time,
        'createAt': time,
        'createBy': alterFan['createBy'],
        'updateBy': alterFan['createBy'],
        'status': 'auditByLead'
    }
    # fan = dict_to_model(Fan, fan)
    # fan = dict_to_model(FanUpdateRecord, fan)
    try:
        # if True:
        async with db.atomic_async():
            bizId = id
            fileNamePrefix = get_save_bizeId(model, figNum, version)
            # fileInfo表先删再增
            # await FileInfo.delete_by_biz_id(bizId)
            await FileInfo.delete_by_biz_id(recordFanId)

            # for fileId in imgDict:
            #     if imgDict[fileId] is not None:
            #         imgList = imgDict[fileId]
            #         for img in imgList:
            #             if type(img) == str:
            #                 # img = img.replace('null','')
            #                 # fileInfo = ast.literal_eval(img)
            #                 fileInfo = json.loads(img)
            #                 # await FileInfo.add(fileInfo)
            #                 patt = r'\-\d{1,}\.'
            #                 pattern = re.compile(patt)
            #                 result = pattern.findall(fileInfo['fileName'])
            #                 # -i.
            #                 i = result[-1]
            #                 fileInfo['fileName'] = fileNamePrefix + '-' + fileNameDict[fileId] + i + fileInfo[
            #                     'fileType']
            #                 fileInfo['bizId'] = recordFanId
            #                 fileInfo['id'] = uuid.uuid1()
            #                 await FileInfo.add(fileInfo)
            #         for img in imgList:
            #             if type(img) != str:
            #                 # else:
            #                 result = await up_file(recordFanId, fileId, fileNamePrefix, [img])
            # raise HTTPException(400, '文件存储失败，详情：' )
            # recordFanId 新增的fanId bizId 变更的这条origin记录的id
            # res = await async_db.execute(
            #     FileInfo.select(
            #         fn.group_concat(FileInfo.fileName).python_value(convert_arr).alias('name')).group_by(
            #         FileInfo.bizId).where(
            #         FileInfo.bizId == bizId).dicts())
            # res = list(res)
            # if len(res) == 0:
            #     nameList = []
            # else:
            #     nameList = res[0]['name']
            for fileId in fileDict:
                if fileDict[fileId] is not None:
                    fileList = fileDict[fileId]
                    # i = 1
                    # 先存未修改的文件 保证新增文件时i不会重复
                    for file in fileList:
                        if type(file) == str:
                            fileInfo = json.loads(file)
                            # 变更新上传的文件
                            if 'bizId' not in fileInfo:
                                await save_file_info(fileInfo, recordFanId, fileId, fileNamePrefix)
                            else:
                                # print('file str')
                                # print(file)
                                # img = img.replace('null','')
                                # fileInfo = ast.literal_eval(img)
                                patt = r'\-\d{1,}\.'
                                pattern = re.compile(patt)
                                result = pattern.findall(fileInfo['fileName'])
                                # -i.
                                i = result[-1]

                                # while fileNamePrefix + '-' + fileNameDict[fileId] + '-' + str(i) + '.' + fileInfo[
                                #     'fileType'] in nameList:
                                #     i = i + 1
                                fileInfo['bizType'] = fileId
                                # fileInfo['fileName'] = fileNamePrefix + '-' + fileNameDict[fileId] + '-' + str(i) + '.' + \
                                #                        fileInfo['fileType']
                                fileInfo['fileName'] = fileNamePrefix + '-' + fileNameDict[fileId] + i + fileInfo[
                                    'fileType']
                                fileInfo['bizId'] = recordFanId
                                fileInfo['id'] = str(uuid.uuid1())
                                await FileInfo.add(fileInfo)
                    # 新增文件查询已存在的namelist插空生成文件名i
                    for file in fileList:
                        if type(file) != str:
                            # else:
                            # print(file)
                            result = await up_file(recordFanId, fileId, fileNamePrefix,
                                                   [file])  # raise HTTPException(400, '文件存储失败，详情：' )
            # await FileInfo.delete_by_biz_id(bizId)

            # perfData 先删再增
            # await PerfData.del_perf_data([id])
            await PerfData.add_perf_datas(perfData)
            # result =await Fan.update_fan(fan)
            # 变更新增一条记录，不影响原来风机数据在审核期间可用/变更期间，原来风机数据不可用
            fanId = await FanUpdateRecord.add_fan_by_dict(fan)
            # fanId = await FanUpdateRecord.add_fan_by_dict(fan)
            version1 = await async_db.execute(
                FanUpdateRecord.select().where(
                    FanUpdateRecord.model == model,
                    FanUpdateRecord.figNum == figNum,
                    FanUpdateRecord.version == version,
                    # FanUpdateRecord.status.in_['passed','pass'] == version,

                ).dicts())
            version1 = len(list(version1))

            await FanUpdateRecordRelp.add(
                {'id': recordFanId, 'type': 'alter', 'version': version1, 'fanId': alterId, 'remark': reason})

            # await AuditRecord.add_audit_record({
            #     'auditBizId': fan['id'],
            #     'userId': updateBy,
            #     'auditType': 'fanAlterAudit',
            # })
            return resp.ok()
    except Exception as e:
        print('e')
        print(e)
        return resp.fail(resp.DataUpdateFail, detail=str(e))


@router.post("/hide", summary="隐藏风机信息", dependencies=[Depends(get_db)])
async def hide_fans(
        del_list: list

) -> Any:
    try:
        # if True:
        async with db.atomic_async():
            result = await async_db.execute(Fan.update({Fan.delete: 1}).where(Fan.id.in_(del_list)).dicts())
            resultRelp = await async_db.execute(
                FanUpdateRecordRelp.select().where(FanUpdateRecordRelp.fanId.in_(del_list)).dicts())
            resultRelp = list(resultRelp)
            del_update_record_list = []
            for item in resultRelp:
                fanUpdateRecord = await FanUpdateRecord.single_by_id(item['id'])
                if fanUpdateRecord['status'] in ['audit', 'auditAlter']:
                    return resp.fail(resp.DataDestroyFail.set_msg('存在未审核的记录！请先审核再删除！'))
                del_update_record_list.append(item['id'])
            print('del_update_record_list')
            print(del_update_record_list)
            result1 = await async_db.execute(FanUpdateRecord.update({FanUpdateRecord.delete: 1}).where(
                FanUpdateRecord.id.in_(del_update_record_list)).dicts())
            return resp.fail(resp.DataDestroyFail)
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    if result != len(del_list):
        return resp.fail(
            resp.DataDestroyFail.set_msg('应删除条数：' + str(len(del_list)) + ',实际删除条数：' + str(result)))
    if result1 != len(del_update_record_list):
        return resp.fail(resp.DataDestroyFail.set_msg(
            '应删除条数：' + str(len(del_update_record_list)) + ',实际删除条数：' + str(result)))
    return resp.ok(data=result)


@router.post("/recover", summary="恢复风机信息", dependencies=[Depends(get_db)])
async def recover_fans(
        del_list: list

) -> Any:
    try:
        # if True:
        async with db.atomic_async():
            result = await async_db.execute(Fan.update({Fan.delete: 0}).where(Fan.id.in_(del_list)).dicts())

            resultRelp = await async_db.execute(
                FanUpdateRecordRelp.select().where(FanUpdateRecordRelp.fanId.in_(del_list)).dicts())
            resultRelp = list(resultRelp)
            recover_update_record_list = []
            for item in resultRelp:
                recover_update_record_list.append(item['id'])
            # print('del_update_record_list')
            # print(del_update_record_list)
            result1 = await async_db.execute(FanUpdateRecord.update({FanUpdateRecord.delete: 0}).where(
                FanUpdateRecord.id.in_(recover_update_record_list)).dicts())

    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))
    if result != len(del_list):
        return resp.fail(resp.DataDestroyFail.set_msg('恢复条数：' + str(result)))
    if result1 != len(recover_update_record_list):
        return resp.fail(resp.DataDestroyFail.set_msg(
            '应恢复条数：' + str(len(recover_update_record_list)) + ',实际恢复条数：' + str(result)))
    return resp.ok(data=result)


@router.post("/delete", summary="删除风机信息", dependencies=[Depends(get_db)])
async def del_fans(del_list: list) -> Any:
    # print("del_list")
    # print(del_list)
    # 删除文件
    for id in del_list:
        fan = await Fan.single_by_id(id)
        model = fan['model']
        figNum = fan['figNum']
        version = fan['version']
        fileDir = '/psad/' + 'fan/' + model
        fileNamePrefix = model + '-' + figNum + '-' + version
        print('fileNamePrefix')
        print(fileNamePrefix)
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
        except Exception as e:
            print(e)
            return resp.fail(resp.DataDestroyFail, detail=str(e))
    try:
        resultRelp = await async_db.execute(
            FanUpdateRecordRelp.select().where(FanUpdateRecordRelp.fanId.in_(del_list)).dicts())
        resultRelp = list(resultRelp)
        del_update_record_list = []
        for item in resultRelp:
            del_update_record_list.append(item['id'])
        print('del_update_record_list')
        print(del_update_record_list)
        for delId in del_update_record_list:
            fanUpdateRecord = await FanUpdateRecord.single_by_id(delId)
            if fanUpdateRecord['status'] in ['audit', 'auditAlter', 'auditByLead']:
                return resp.fail(resp.DataDestroyFail.set_msg('存在未审核的记录！请先审核再删除！'))
        async with db.atomic_async():
            await FileInfo.delete_by_biz_id_list(del_list)
            await PerfData.del_perf_data(del_list)
            # await FanUpdateRecordRelp.del_perf_data(del_list)

            deleteNum = await FanUpdateRecord.del_fan(del_update_record_list)
            if deleteNum != len(del_update_record_list):
                raise Exception(
                    'FanUpdateRecord 应删除条数：' + str(len(del_update_record_list)) + '条,实际删除条数：' + str(
                        deleteNum) + '条')
            await async_db.execute(FanUpdateRecordRelp.delete().where(FanUpdateRecordRelp.fanId.in_(del_list)))
            deleteNum = await Fan.del_fan(del_list)
            if deleteNum != len(del_list):
                raise Exception(
                    'Fan 应删除条数：' + str(len(del_update_record_list)) + '条,实际删除条数：' + str(deleteNum) + '条')
            await async_db.execute(FanUpdateRecordRelp.delete().where(FanUpdateRecordRelp.fanId.in_(del_list)))
            await async_db.execute(AuditRecord.delete().where(AuditRecord.auditBizId.in_(del_list)))
            await async_db.execute(AuditRecord.delete().where(AuditRecord.auditBizId.in_(del_update_record_list)))
            # print(result)
            # await FileInfo.delete_by_biz_id(get_save_bizeId(model, figNum, version))
    except Exception as e:
        print(e)
        return resp.fail(resp.DataDestroyFail, detail=str(e))

    return resp.ok()


# /{model}

#


@router.post("/detail", summary="查询风机信息", dependencies=[Depends(get_db)])
async def get_fan_info(
        id: str
) -> Any:
    # print('model:'+model)
    result = await Fan.single_by_id(id)
    if not result:
        result = await FanUpdateRecord.single_by_id(id)
    # print('result')
    # print(result)
    if result is None:
        return resp.fail(resp.DataNotFound.set_msg('查询失败，未找到风机信息！'))
        # return resp.ok(data=result)
    # if result['motor_speed_min'] != None:
    #     result['motor_speed'] = str(result['motor_speed_min']) + \
    #         '/'+str(result['motor_speed'])
    # print("result['img3d']")
    # print(result['img3d'])
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
    # result["aerodynamicSketch"] = 'error'
    # for path in result["technicalFile"]["aerodynamicSketch"]:
    #     if path.split('.')[-1] == 'pdf':
    #         result["aerodynamicSketch"] = path

    # result["aerodynamicSketch"] = result["technicalFile"]["aerodynamicSketch"]
    result["technicalFile"].pop('aerodynamicSketch')

    result['technicalFile']['labReport'] = await FileInfo.fuzzy_query({'bizId': bizId, 'bizType': 'labReport'})
    result['technicalFile']['designSpecification'] = await FileInfo.fuzzy_query(
        {'bizId': bizId, 'bizType': 'designSpecification'})
    result['outlineFile'] = await FileInfo.fuzzy_query({'bizId': bizId, 'bizType': 'outlineFile'})
    result['aerodynamicSketch'] = await FileInfo.fuzzy_query({'bizId': bizId, 'bizType': 'aerodynamicSketch'})
    # 检查“风机型号”键是否重复
    # fanList = await async_db.execute(
    #     Fan.select().where(Fan.model == model,).dicts())
    # fanList = list(fanList)
    #
    # if len(fanList) >= 1:
    #     isCopy = 'copy'
    # else:
    #     isCopy = None
    # result['type'] = isCopy
    fanList = await async_db.execute(
        FanUpdateRecordRelp.select().where(FanUpdateRecordRelp.id == id, FanUpdateRecordRelp.type == 'copy').dicts())

    fanList = list(fanList)
    if len(fanList) >= 1:
        isCopy = 'copy'
    else:
        isCopy = None

    result['type'] = isCopy
    return resp.ok(data=result)


@router.post('/import/excel', dependencies=[Depends(get_db)])
async def importExcel(fan_list: list):
    # UploadFile = Form(...)
    print('/import/excel')
    for fan in fan_list:
        try:
            result = await Fan.add_fan_by_dict(
                fan
            )
            print('result')
            print(result)
        except Exception as e:
            print(e)
            return resp.fail(resp.DataStoreFail, detail=str(e))
    return resp.ok()


@router.get("/test", summary="多项式拟合曲线", dependencies=[Depends(get_db)])
def test():
    data = {
        'flowRate': [0.985, 1.985, 2.985, 3.985, 4.985, 5.985, 6.985, 7.985, 8.985],
        'pressure': [1249.4, 1207.1, 1184.9, 1157, 1127.6, 1057.3, 970.53, 608.24, 257.9],
        'shaftPower': [2.0981, 2.1866, 2.1596, 2.2219, 2.2305, 2.2207, 2.2639, 2.1696, 1.899],
        'fanPower': [59.5, 61.8, 63.9, 69.1, 70.2, 71.4, 69.8, 54.2, 29.3],
    }
    x = data['flowRate']
    y = data['fanPower']
    an = np.polyfit(x, y, 2)
    print(an)
    print(an[0])
    # y2 = an[0]*x*x+an[1]*x+an[2]
    # print(y2)

    y2 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    index = 0
    for i in x:
        y2[index] = an[0] * i ** 2 + an[1] * i + an[2]
        index = index + 1

    print(y2)
    p1 = np.poly1d(an)
    print(p1)
    correlation = np.corrcoef(y, y2)[0, 1]  # 相关系数
    r = correlation ** 2  # R方
    print('R')
    print(r)
    return resp.ok(data=an.tolist())


# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
# from io import BytesIO
# import xlsxwriter
# import time
# 需要新装一个xlsxwriter==3.1.9库
# @router.get("/testxlsx", summary="风机信息性能曲线模板生成")
# async def download_excel():
#
#     for i in range(5):
#         print(i)
#         time.sleep(1)
#
#     output = BytesIO()  # 在内存中创建一个缓存流
#     workbook = xlsxwriter.Workbook(output)
#     worksheet = workbook.add_worksheet()
#     worksheet.write(0, 0, 'ISBN')
#     worksheet.write(0, 1, 'Name')
#     worksheet.write(0, 2, 'Takedown date')
#     worksheet.write(0, 3, 'Last updated')
#     workbook.close()
#     output.seek(0)
#
#     headers = {
#         'Content-Disposition': 'attachment; filename="filename.xlsx"'
#     }
#     return StreamingResponse(output, headers=headers)
