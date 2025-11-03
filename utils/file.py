import shutil
import os
import time
import uuid
from datetime import datetime
from typing import Union, List

import pytz
import requests
from fastapi import UploadFile, HTTPException
from peewee import fn

from common.session import db, async_db
from core.config import settings
from models.file_info import FileInfo
from schemas.response import resp
from utils.tools_func import validateStr, convert_arr

fileNameDict = {
    'img3d': '三维图',
    'outlineFile': '外形尺寸图',
    'labReport': '实验报告',
    'designSpecification': '设计说明书',
    'aerodynamicSketch': '气动略图'
}

# UploadFileUrl = 'http://172.16.50.127:8080/api/minIO/upload'

contentTypeDict = {
    'jpg': 'image/jpg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'dwg': 'image/vnd.dwg',
    'doc': 'application/msword',
    'pdf': 'application/pdf',

}


async def save_file_info(result, bizId: str, bizType: str, fileNamePrefix):
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
    i = 1

    while fileNamePrefix + '-' + fileNameDict[bizType] + '-' + str(i) + '.' + result['fileFormat'] in nameList:
        i = i + 1
        # print("r['viewUrl']")
        # print(r['viewUrl'])
    fileInfo = {
            'id': uuid.uuid1(),
            'bizId': bizId,
            'bizType': bizType,
            'fileName': fileNamePrefix + '-' + fileNameDict[bizType] + '-' + str(i) + '.' + result['fileFormat'],
            'newName': result['fileName'],
            'fileType': result['fileFormat'],
            'fileSize': result['fileSize'],
            'downloadUrl': result['downloadUrl'],
            'viewUrl': result['viewUrl'],
            'createAt': datetime.strftime(
                datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S'),
            # 'updateAt': datetime.strftime(
            #     datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        }
    try:
        # if True:
        async with db.atomic_async():
            await FileInfo.add(fileInfo)
        return True
    except Exception as e:
        raise HTTPException(400, '文件存储失败，详情：' + str(e))


async def up_file(bizId: str, bizType: str, fileNamePrefix, fileList: List[Union[UploadFile, dict]]):
    # Url,
    '''
    用于POST上传文件以及提交参数
    @ Url 上传接口
    @ FilePath 文件路径
    @ data 提交参数 {'key':'value', 'key2':'value2'}
    '''
    print('fileList')
    print(fileList)
    files = []
    for file in fileList:
        byteFile = await file.read()
        files.append(('files',
                      (file.filename, byteFile, file.content_type)))
        # if type(file) == UploadFile:
        # 直接上传二进制文件流
        # file={filename:string,content_type:.xxx,byteFile:bytes}
        # elif type(file) == dict:
        #     # print(file)
        #     byteFile = file['byteFile']
        #     files.append(('files',
        #               (file['filename'], byteFile,contentTypeDict[file['content_type']])))

        # print('files'), file['content_type']
        # print(files)
    try:
        # if True:
        #     response = requests.post(settings.UPLOAD_FILE_URL, files=files)
        response = requests.post(os.getenv('UPLOAD_FILE_URL'), files=files)
        result = response.json()
        print('result')
        print(result)
        if result['code'] != 200:
            # print('文件存储失败，详情：' + result)

            raise HTTPException(400, '文件存储失败，详情：')
    except Exception as e:
        print('文件存储失败，详情：' + str(e))
        raise HTTPException(400, '文件存储失败，详情：' + str(e))
    # return result['data']

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
    i = 1
    for r in result['data']:
        while fileNamePrefix + '-' + fileNameDict[bizType] + '-' + str(i) + '.' + r['fileFormat'] in nameList:
            i = i + 1
        # print("r['viewUrl']")
        # print(r['viewUrl'])
        fileInfo = {
            'id': uuid.uuid1(),
            'bizId': bizId,
            'bizType': bizType,
            'fileName': fileNamePrefix + '-' + fileNameDict[bizType] + '-' + str(i) + '.' + r['fileFormat'],
            'newName': r['fileName'],
            'fileType': r['fileFormat'],
            'fileSize': r['fileSize'],
            'downloadUrl': r['downloadUrl'],
            'viewUrl': r['viewUrl'],
            'createAt': datetime.strftime(
                datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S'),
            # 'updateAt': datetime.strftime(
            #     datetime.now(pytz.timezone('Asia/Shanghai')), '%Y-%m-%d %H:%M:%S')
        }
        try:
            # if True:
            async with db.atomic_async():
                await FileInfo.add(fileInfo)
            return True
        except Exception as e:
            raise HTTPException(400, '文件存储失败，详情：' + str(e))

            # return resp.fail(resp.DataStoreFail, detail=str(e))


def get_url(category: str, model: str, filename: Union[int, str] = None):
    model = validateStr(model)
    filename = str(filename)
    path = '/psad/' + category + '/' + model
    print("path")
    print(path)
    result = []
    if os.path.isdir(path):
        for f in os.listdir(path):
            # print('f')
            # print(f)
            i = 1
            if (f.find(filename) == 0):
                # path = settings.SERVER_URL+'/api/download'+path+'/'+f   +'?v='+str(int(time.time()))
                result.append('/api/download' + path + '/' +
                              f)

            else:
                continue
        if len(result) == 0:
            # return 'error'
            return []

        # if len(result)==1:
        #     return result[0]
        return result
    else:
        print("文件路径 " + path + " 不存在")
        # return 'error'
        return []

    # print("path")
    # print(path)


# def get_url(category: str,   model: str, fileType: str,  filename: Union[int, str] = None):

#     filename = str(filename)
#     path = '/psad/'+category + '/'+model+'/'+fileType
#     print("path")
#     print(path)
#     if os.path.isdir(path):
#         for f in os.listdir(path):
#             print('filename')
#             print(filename)
#             if (f.find(filename) == 0):
#                 # path = settings.SERVER_URL+'/api/download'+path+'/'+f
#                 path = '/api/download'+path+'/'+f
#                 return path
#             else:
#                 continue
#         return 'error'
#     else:
#         print("文件路径 "+path+" 不存在")
#         return 'error'

#     # print("path")
#     # print(path)


'''
description: 生成存储文件名
param {str} model
param {str} figNum
param {str} version
param {str} fileId
param {int} fileNum
param {*} file
return {*}
'''


def get_file_name(model: str, figNum: str, version: str, fileId: str):
    model = validateStr(model)
    fileName = model + '-' + figNum + '-' + version + '-' + fileNameDict[fileId]

    return fileName


def get_save_file_name(model: str, figNum: str, version: str, fileId: str, fileNum: int, file):
    # / : * " < > | ？
    # model.find('/')
    try:
        fileType = file.filename.split('.')[-1]

    except Exception as e:
        fileType = file.name.split('.')[-1]

    except Exception as e:

        print('无法获取传入文件文件名')
        return None
    model = validateStr(model)
    if fileNum == '*':
        fileName = model + '-' + figNum + '-' + version + \
                   '-' + fileNameDict[fileId] + '-' + '*'
        return fileName
    elif fileNum == 0:
        fileName = model + '-' + figNum + '-' + version + '-' + \
                   fileNameDict[fileId] + '.' + fileType
        return fileName
    else:
        fileNum = str(fileNum)

    fileName = model + '-' + figNum + '-' + version + '-' + fileNameDict[fileId] + '-' + \
               fileNum + '.' + fileType
    return fileName


def img_str_to_url_list(imgStr: str):
    # print('imgStr:')
    # print(imgStr)
    if (imgStr is None) or imgStr == '':
        print('error')
        return []

    temp = imgStr.split(',')
    result = []
    if (len(temp) == 0):
        return []
    for t in temp:
        result.append('/api/download' + t)
    return result


# +'?v='+str(int(time.time()))

# 较两个文件的内容是否相同
# tempPath = dir+'/temp-'+name
# # print('tempPath')
# # print(tempPath)
# res = await file.read()
# with open(tempPath, "wb") as f:
#     f.write(res)
# result = cmp_file(filePath, tempPath)
# if result:
#     os.remove(tempPath)
#     pass
# else:
#     print('文件不同,覆盖 ')
#     os.remove(filePath)
#     res = await f2.read()
#     with open(filePath, "wb") as f2:
#         f2.write(res)
#     os.remove(tempPath)


def cmp_file(f1, f2):
    st1 = os.stat(f1)
    st2 = os.stat(f2)

    # 比较文件大小
    if st1.st_size != st2.st_size:
        return False

    bufsize = 8 * 1024
    with open(f1, 'rb') as fp1, open(f2, 'rb') as fp2:
        while True:
            b1 = fp1.read(bufsize)  # 读取指定大小的数据进行比较
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                return True
