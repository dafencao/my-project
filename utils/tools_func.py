import inspect
import json
import decimal
import datetime
import os
import threading
from typing import Union
import re

import pytz
# coding=UTF-8
import xlrd
import xlwt
from xlutils.copy import copy

import re

tz = pytz.timezone('Asia/Shanghai')

def validateStr(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title


def _alchemy_encoder(obj):
    """
    处理序列化中的时间和小数
    :param obj:
    :return:
    """
    if isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


def serialize_sqlalchemy_obj(obj) -> Union[dict, list]:
    """
    序列化fetchall()后的sqlalchemy对象
    https://codeandlife.com/2014/12/07/sqlalchemy-results-to-json-the-easy-way/
    :param obj:
    :return:
    """
    if isinstance(obj, list):
        # 转换fetchall()的结果集
        return json.loads(json.dumps([dict(r) for r in obj], default=_alchemy_encoder))
    else:
        # 转换fetchone()后的对象
        return json.loads(json.dumps(dict(obj), default=_alchemy_encoder))


def remove_dir(dir: str):
    if (os.path.isdir(dir)):
        for p in os.listdir(dir):
            remove_dir(os.path.join(dir, p))
        if (os.path.exists(dir)):
            os.rmdir(dir)
    else:
        if (os.path.exists(dir)):
            os.remove(dir)


def name_convert_to_camel(name: str) -> str:
    """下划线转驼峰(小驼峰)"""

    return re.sub(r'(_[a-z])', lambda x: x.group(1)[1].upper(), name)


def name_convert_to_snake(name: str) -> str:
    """驼峰转下划线"""
    if '_' not in name:
        name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    else:
        raise ValueError(f'{name}字符中包含下划线，无法转换')
    return name.lower()


def name_convert(name: str) -> str:
    """驼峰式命名和下划线式命名互转"""
    is_camel_name = True  # 是否为驼峰式命名
    if '_' in name and re.match(r'[a-zA-Z_]+$', name):
        is_camel_name = False
    elif re.match(r'[a-zA-Z]+$', name) is None:
        raise ValueError(f'Value of "name" is invalid: {name}')
    return name_convert_to_snake(name) if is_camel_name else name_convert_to_camel(name)


def write_excel_xls(path, sheet_name, header, data):
    '''写入xls文件
    Args:
        path (str): 保存路径
        sheet_name (str): 文件名
        header (list): 表头
        data (list): 保存数据
    '''
    print('data')
    print(data)
    print(len(data))
    dir = '/'.join(path.split('/')[:-1])
    name = path.split('/')[-1]
    if not os.path.exists(dir):
        os.makedirs(dir)
    index = len(data)  # 获取需要写入数据的行数
    print('index')
    print(index)

    workbook = xlwt.Workbook()  # 新建一个工作簿
    sheet = workbook.add_sheet('性能曲线数据')  # 在工作簿中新建一个表格
    for j in range(0, len(header)):  # 存表头
        sheet.write(0, j, header[j])
    for i in range(0, index):
        for j in range(0, len(data[i])):
            sheet.write(i+1, j, data[i][j])  # 向表格中写入数据（对应的行和列）
    workbook.save(path)  # 保存工作簿
    print("xls格式表格写入数据成功！")


def write_excel_xls_append(path, value):
    index = len(value)  # 获取需要写入数据的行数
    workbook = xlrd.open_workbook(path)  # 打开工作簿
    sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
    worksheet = workbook.sheet_by_name(sheets[0])  # 获取工作簿中所有表格中的的第一个表格
    rows_old = worksheet.nrows  # 获取表格中已存在的数据的行数
    new_workbook = copy(workbook)  # 将xlrd对象拷贝转化为xlwt对象
    new_worksheet = new_workbook.get_sheet(0)  # 获取转化后工作簿中的第一个表格
    for i in range(0, index):
        for j in range(0, len(value[i])):
            # 追加写入数据，注意是从i+rows_old行开始写入
            new_worksheet.write(i+rows_old, j, value[i][j])
    new_workbook.save(path)  # 保存工作簿
    print("xls格式表格【追加】写入数据成功！")


def read_excel_xls(path):
    workbook = xlrd.open_workbook(path)  # 打开工作簿
    sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
    worksheet = workbook.sheet_by_name(sheets[0])  # 获取工作簿中所有表格中的的第一个表格
    for i in range(0, worksheet.nrows):
        for j in range(0, worksheet.ncols):
            print(worksheet.cell_value(i, j), "\t", end="")  # 逐行逐列读取数据
        print()


book_name_xls = 'xls格式测试工作簿.xls'

sheet_name_xls = 'xls格式测试表'

header = ["姓名", "性别", "年龄", "城市", "职业"]

value1 = [["张三", "男", "19", "杭州", "研发工程师"],
          ["李四", "男", "22", "北京", "医生"],
          ["王五", "女", "33", "珠海", "出租车司机"],
          ["Tom", "男", "21", "西安", "测试工程师"],
          ["Jones", "女", "34", "上海", "产品经理"],
          ["Cat", "女", "56", "上海", "教师"],]

rolePremission = {
    1: {
        '/fan/3',
        '/fan/2',
        '/fan/4',
    },
    # 营销人员
    2: {
        # '/fan/2',
    },
    # 研发人员
    3: {
        '/fan/3',
        '/fan/2',
    }
}

# write_excel_xls(book_name_xls, sheet_name_xls, header, value1)
# write_excel_xls_append(book_name_xls, value1)
# write_excel_xls_append(book_name_xls, value2)
# read_excel_xls(book_name_xls)


def convert_arr(s):
    # 字符串转数组并去重
    if s:
        s = list(set(s.split(',')))
    return s


def convert_num_arr(s):
    # 字符串转数组并去重
    if s:
        s = list(set(s.split(',')))
        for i in range(len(s)):
            s[i] = int(s[i])
    if s:
        return s
    else:
        return []

def convert_num_float_arr(s):
    # 字符串转数组并去重
    if s:
        s = list(s.split(','))
        for i in range(len(s)):
            s[i] = float(s[i])
    if s:
        return s
    else:
        return []
class Singleton(type):
    _instance_lock = threading.Lock()
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def __call__(cls, *args, **kwargs):
        with cls._instance_lock:
            if not hasattr(cls, '_instance'):
                cls._instance = super().__call__(*args, **kwargs)
        return cls._instance