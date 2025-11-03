import os
from typing import Any, Optional, Union, List

import pytz
import requests
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from core import security
from models.fan import Fan, FanCategory
from common import deps, logger
from schemas.response import resp
from schemas.request import sys_fan_schema
from starlette.responses import FileResponse

from fastapi import status as http_status
from fastapi.responses import JSONResponse, Response
from datetime import datetime

from utils.tools_func import tz

router = APIRouter()


# 根据项目号、文件类号查询本地文件的信息，包含：成功/失败， 文件名， 文件相对路径，创建时间
@router.post("/api/findFileInfo/{path:path}")
async def find_docInfo_by_path(path: str):
    docInfo = {
        "exist": False,
        "docDir": "/",
        "docName": "No file exist",
        "createTime": str(datetime.min)
    }

    if os.path.exists(path):
        timestamp = os.path.getctime(path)
        docInfo["createTime"] = datetime.utcfromtimestamp(
            timestamp).strftime("%Y-%m-%d")
        docInfo = {
            "exist": True,
            "docDir": path,
            "docName": path.split('/')[-1],
            "createTime": str(datetime.min)
        }
    return resp.ok(data=docInfo)


# 根据项目号、文件类号查询本地文件的信息，包含：成功/失败， 文件名， 文件相对路径，创建时间
async def find_docInfo(projectID: str, docType: int, pathType: str):
    docInfo = {
        "exist": False,
        "docDir": "/",
        "docName": "No file exist",
        "createTime": str(datetime.min)
    }
    docInfoList = []
    filePath = await get_path(pathType)
    docType = str(docType)
    # docDir = filePath + projectID[2:6] + '/'+projectID + '/'
    if pathType == 'alter':
        docDir = filePath + projectID[2:6]+'/' + \
            projectID+'/alter/'
        # +'bg' + projectID[2:]+str(recordCount).zfill(2)+'/'
    else:
        docDir = filePath + projectID[2:6]+'/'+projectID+'/'
    if not os.path.exists(docDir):
        os.makedirs(docDir)
    if os.path.isdir(docDir):
        for docName in os.listdir(docDir):
            if docName == 'alter':
                continue
            data = [i for i in docName.split("-") if i not in ["", " "]]
            pID, docT = data[:2]
            docT = docT.split('.')[0]
            if pathType == 'alter':
                recordCount = await db.DB.projectChange.count_documents({"projectID": projectID})
                if projectID[2:] == pID[2:len(projectID)] and str(recordCount).zfill(2) == pID[-2:] and docType == docT:
                    docInfo["exist"] = True
                    docInfo["docDir"] = docDir[1:]  # docDir[2:]
                    docInfo["docName"] = docName
                    docInfo["docDir"] = docInfo["docDir"] + docInfo["docName"]
                    timestamp = os.path.getctime(docDir + docName)
                    docInfo["createTime"] = datetime.utcfromtimestamp(
                        timestamp).strftime("%Y-%m-%d")
                    break
                else:
                    continue
            try:
                # and docT[len(docType)] == ".":

                # [:len(docType)]:
                if projectID[2:] == pID[2:len(projectID)] and docType == docT:
                    # print('docInfo changed')
                    docInfo["exist"] = True
                    docInfo["docDir"] = docDir[1:]  # docDir[2:]
                    docInfo["docName"] = docName
                    timestamp = os.path.getctime(docDir + docName)
                    docInfo["createTime"] = str(datetime.utcfromtimestamp(
                        timestamp).strftime("%Y-%m-%d"))
                    docInfo["docDir"] = docInfo["docDir"] + docInfo["docName"]

                    if docType in ['3', '4', '5', '6', '7']:
                        # print('append docName'+docName)
                        # print(docInfo)
                        docInfoList.append({
                            "exist": True,
                            "docName": docName,
                            "createTime": str(datetime.utcfromtimestamp(
                                timestamp).strftime("%Y-%m-%d")),
                            "docDir": docDir[1:] + docInfo["docName"],
                        })
                        # print(docInfoList)
                        continue
                    break
            except Exception as e:
                print('error')
                continue
    if docType in ['3', '4', '5', '6', '7']:
        return docInfoList
    return docInfo


@router.get("/api/preview/{path:path}")
async def preview(path: str):
    pathArr = path.split('/')
    pathArr[-1] = 'preview-'+pathArr[-1].split('.').pop(0)+'.pdf'
    prePath = '/'+'/'.join(pathArr)
    path = '/'+path
    fileType = path.split('.').pop(1)
    result = {"success": False,
              "message": "dir: src/ is not allowed to download!"}
    if "src/" in path[:5]:
        return resp.fail(resp.PermissionDenied)

    if not os.path.exists(path):
        result["message"] = "file does not exist."
        return resp.fail(resp.DataNotFound, "file does not exist.")
    curPath = os.path.abspath(os.path.dirname(__file__))
    rootPath = curPath[:curPath.find("项目名\\")+len("项目名\\")]
    if os.path.exists(prePath):
        return FileResponse(prePath)
    if fileType == 'doc':
        if os.path.exists(path):
            # result = await createpdf(path, prePath)
            # print('result')
            # print(result)
            # if result == False:
            #     return FileResponse(path)
            return FileResponse(prePath)
        return resp.ok(data=result)
        # Response(content=dumps({'success': result}),
        #          media_type="application/json")

    # print('Response(prePath)')
    return FileResponse(path)  # path_join("../", path)

# ,  dependencies=[Depends(deps.save_user_action)]

#


@router.get("/download/{path:path}")
async def download(path: str, v: str = None):
    #  token: Optional[str] = Header(..., description="登录token")
    print('/api/download/'+path)
    path = path.split('?')[0]
    print('/api/download/'+path)

    if path is None:
        return resp.fail(resp.DataNotFound.set_msg("filepath does not exist."))

    path = '/'+path
    print(path)

    print("os.path.exists(path)")
    print(os.path.exists(path))
    result = {"success": False,
              "message": "dir: src/ is not allowed to download!"}
    if "src/" in path[:5]:
        return resp.fail(resp.PermissionDenied)
    if not os.path.exists(path):
        result["message"] = "file does not exist."
        return resp.fail(resp.DataNotFound.set_msg("文件不存在"))

    return FileResponse(path)
    # file_like = open('/psad/img/风机/category/model1', mode="r")
    # print("file_like")
    # print(file_like)
    # return FileResponse(file_like, media_type='application/json')

    # file_like = open(path, mode="rb")
    # return StreamingResponse(file_like, media_type="image/jpg")


def get_save_dir(category: str,   model: str,  fileType: str,   filename: str):
    fileForm = filename.split('.')[-1]

    # if fileForm in ['png', 'jpg', 'jpeg', 'gif']:
    #     fileType = 'img'
    #     return '/psad/'+category + '/'+model+'/'+'img/'
    # else:
    return '/psad/'+category + '/'+model+'/'+fileType+'/'


@router.post("/upload_doc", summary="根据风机型号、上传文件类型 上传单个文件", name="上传单个文件")
async def upload_doc(file: UploadFile = File(...), model: str = Form(...), fileType: int = Form(...)):
    # docDir = await get_path(pathType, model)
    docDir = '/psad/'+model

    result = dict()
    start = datetime.now(pytz.timezone('Asia/Shanghai'))

    fileForm = file.filename.split('.')[-1]
    docName = "{}-{}.{}".format(model, fileType, fileForm)
    docPath = docDir + docName
    try:
        if not os.path.exists(docDir):
            os.makedirs(docDir)
        # 检查删除之前存在的同类文件
        # else:
        res = await file.read()
        with open(docPath, "wb") as f:
            f.write(res)
            result["time"] = str(datetime.now(pytz.timezone('Asia/Shanghai')) - start)
            result["success"] = True
        # await delete_doc(pathType, model, docName)
        return resp.ok(data=FileResponse(docPath))
    except Exception as e:
        result = {
            "success": False,
            "message": str(e),
            "time": str(datetime.now(pytz.timezone('Asia/Shanghai')) - start),
            'filename': file.filename
        }
        return resp.fail(resp.DataStoreFail)


# @router.get("/api/delete_doc")
# async def test():
#     await delete_doc('project', 'xm202200001', 'xm202200001-0.docx')


# 删除一个文件夹下除传入的文件类型以外 同名不同文件类型的文件 先上传覆盖再删除避免文件丢失
# isExcept 是否忽略不同文件类型的的覆盖及保留

@router.post("/api/delete_doc")
async def delete_doc1(item_dict: dict):
    return await delete_doc(item_dict['pathType'], item_dict['ID'], item_dict['docName'], True)


async def delete_doc(pathType: str, ID: str, docName: str, isExcept: bool = False):
    result = {
        "success": True,
        "message": "dictory does not exist."
    }
    docDir = await get_path(pathType, ID)
    fileForm = docName.split('.').pop(1)
    if not os.path.isdir(docDir):
        return Response(content=dumps(result), media_type="application/json")
    else:
        delPath = docDir+docName.split('.').pop(0)+'.*'
        delPreviewPath = docDir+'preview-'+docName.split('.').pop(0)+'.pdf'

        print('delPath')
        print(delPath)
        print('delPreviewPath')
        print(delPreviewPath)
        for file in iglob(delPath):
            if file.split('.').pop(1) != fileForm:
                print('remove_file')
                print(file)

                os.remove(file)
            if isExcept:
                os.remove(file)
        if os.path.exists(delPreviewPath):
            os.remove(delPreviewPath)

        result["message"] = 'delete successful'
        return Response(content=dumps(result), media_type="application/json")


# @router.post("/api/projects/delete_doc")
# async def delete_project_doc(ID: str = Form(...), docType: int = Form(-1), pathType: str = Form(...), ept: str = Form("")):
#     result = {
#         "success": False,
#         "message": "dictory does not exist."
#     }
#     filePath = await get_path(pathType)
#     docDir = filePath + ID[2:6] + "/"+ID+'/'
#     if not os.path.isdir(docDir):
#         return Response(content=dumps(result), media_type="application/json")
#     try:
#         if docType == -1:
#             for docName in os.listdir(docDir):
#                 (checkedID, checkedType), checkedEpt = docName.split(
#                     "-"), docName.split(".")[-1]
#                 if ID[2:] == checkedID[2:len(ID)] and checkedEpt != ept:
#                     os.remove(docDir + docName)
#         else:
#             docType = str(docType)
#             for docName in os.listdir(docDir):
#                 (checkedID, checkedType), checkedEpt = docName.split(
#                     "-"), docName.split(".")[-1]
#                 if ID[2:] == checkedID[2:len(ID)] and checkedEpt != ept and docType == checkedType[:len(docType)]:
#                     os.remove(docDir + docName)
#         return Response(content=dumps({"success": True, }), media_type="application/json")
#     except Exception as e:
#         result["message"] = str(e)
#         return Response(content=dumps(result), media_type="application/json")


# 通过项目ID和文件类别获取文件详细信息 下载路径  Get file info by id and type
@router.post("/api/projects/query_docs")
async def query_docs(item_data: dict):
    result = {
        "success": False,
        "message": ""
    }
    projectID, docTypes = item_data["ID"], item_data["docTypes"]
    fileType = 'project'
    try:
        fileType = item_data['fileType']
    except Exception as e:
        if type(e) == 'KeyError':
            fileType = 'project'
    if not projectID:
        result["message"] = "projectID:{} is null.".format(projectID)
        return Response(content=dumps(result), media_type="application/json")
    if not docTypes:
        result["message"] = "docTypes:{} is null.".format(docTypes)
        return Response(content=dumps(result), media_type="application/json")

    if type(docTypes) is not list:
        docTypes = [docTypes]
    result = []
    for docType in docTypes:
        docInfo = await find_docInfo(projectID, docType, pathType=fileType)
        # print('docInfo')
        # print(docInfo)
        # docInfo["docDir"] = docInfo["docDir"] + docInfo["docName"]
        # docInfo["createTime"] = str(docInfo["createTime"])[:10]
        result.append(docInfo)
    return Response(content=dumps(result), media_type="application/json")


# @router.post('/api/import_excel')
# async def importExcel(file_import: UploadFile = Form(...)):
#     print(file_import)
#     result = {
#         "success": True,
#         'filename': file_import.filename
#     }
#     return Response(content=dumps(result), media_type="application/json")
