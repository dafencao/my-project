
import glob
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Form,   UploadFile, File
from api.v1.file import get_save_dir
from common.session import get_db

from core import security
from models.fan import Fan, FanCategory
from models.fan_perf_data import PerfData
from schemas.response import resp
from schemas.request import sys_fan_schema
from playhouse.shortcuts import model_to_dict

from fastapi import status as http_status
from fastapi.responses import JSONResponse, Response, FileResponse
from playhouse.shortcuts import model_to_dict
from utils.tools_func import remove_dir
from peewee import fn
import numpy as np
# import matplotlib.pyplot as plt
router = APIRouter()


@router.post("/show/list", summary="获取性能曲线数据", dependencies=[Depends(get_db)])
async def get_perf_datas(modelList: list) -> Any:
    print('perf modelList')
    print(modelList)
    resultList = {}
    for model in modelList:
        tempModel = None
        if model.find(')') != -1:
            tempModel = model
            model = model.split(')')[1]
            print(tempModel)
        try:
            data =await PerfData.get_perf_data_by_fan_id(model)
            perfData = {}
            for item in data:
                for key in item:
                    if key not in perfData.keys():
                        perfData[key] = []
                    perfData[key].append(item[key])
            if 'id' in perfData.keys():
                perfData.pop('id')
            if 'model_id' in perfData.keys():
                perfData.pop('model_id')

        except Exception as e:
            print(e)
            return resp.fail(resp.DataNotFound, detail=str(e))
        if tempModel:
            resultList[tempModel] = perfData
        else:
            resultList[model] = perfData
    return resp.ok(data=resultList)


# /{model}


@router.post("/detail", summary="查询性能曲线数据,按字段归类", dependencies=[Depends(get_db)])
async def get_perf_data(id: str) -> Any:

    # print('model')
    # print(model)
    try:
        data =await PerfData.get_perf_data_by_fan_id(id)
        # print('data')
        # print(data)
        if len(data) == 0:
            return resp.ok(data={})

    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))
    # print('data')
    # print(data)
    perfData = {}
    for item in data:
        for key in item:
            if key not in perfData.keys():
                perfData[key] = []
            perfData[key].append(item[key])
    # print('perfData')
    # print(perfData)
    if 'id' in perfData.keys():
        perfData.pop('id')
    if 'modelId' in perfData.keys():
        perfData.pop('modelId')
    if 'createAt' in perfData.keys():
        perfData.pop('createAt')
    if 'updateAt' in perfData.keys():
        perfData.pop('updateAt')
    return resp.ok(data=perfData)

# /{model}

#


@router.post("/show", summary="查询性能曲线数据", dependencies=[Depends(get_db)])
async def get_perf_data(id: str) -> Any:

    print('id')
    print(id)
    try:
        data =await PerfData.get_perf_data_by_fan_id(id)
        # print('data')
        # print(data)
        if len(data) == 0:
            return resp.ok(data=[])

    except Exception as e:
        print(e)
        return resp.fail(resp.DataNotFound, detail=str(e))

    return resp.ok(data=data)


@router.post("/add", summary="新增性能曲线数据")
def add_perf_datas(
    perfData: dict

) -> Any:
    # model = data['model']
    # perfData = eval(data)
    # print('model')
    # print(model)
    print('perfData')
    print(perfData)
    pass


# group_by_field
async def func_get_perf_data_by_fan_id(id: str) :

    try:
        data = await PerfData.get_perf_data_by_fan_id(id)
        # print('data')
        # print(data)
        if len(data) == 0:
            return {}

    except Exception as e:
        print(e)
        return {}
    # print('data')
    # print(data)
    perfData = {}
    for item in data:
        for key in item:
            if key not in perfData.keys():
                perfData[key] = []
            perfData[key].append(item[key])
    # print('perfData')
    # print(perfData)
    # print(type(perfData))
    # print('perfData[motorSpeed]')
    # print(perfData['motorSpeed'])
    # if 'id' in perfData.keys():
    #     perfData.pop('id')
    # if 'model_id' in perfData.keys():
    #     perfData.pop('model_id')
    return perfData
