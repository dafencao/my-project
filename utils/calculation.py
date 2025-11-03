'''
Descripttion: 
version: 
Author: congsir
Date: 2023-03-27 09:01:55
LastEditors: Please set LastEditors
LastEditTime: 2023-04-24 16:15:05
'''
import math

import numpy as np


def get_specific_speed(motorSpeed: float,
                       flowRate: float,
                       fullPressure: float):
    specificSpeed = (motorSpeed * 5.54 * math.pow(flowRate, 0.5)
                     ) / math.pow(fullPressure, 0.75)
    return float(format(specificSpeed, '.3f'))


def fit_perf_data_by_motorSpeed(flowRateData: list, fullPressureData: list, staticPressureData: list,  shaftPower: list, motorSpeed: float, originMotorSpeed: float):
    # print('flowRateData')
    # print(flowRateData)
    # print('pressureData')
    # print(pressureData)
    sdfMs = motorSpeed / originMotorSpeed
    # print('impellerDia')
    # print(impellerDia)
    # print('originImpellerDia')
    # print(originImpellerDia)
    # print('sdfImp')
    # print(sdfImp)
    smiliarFlowRate = []
    smiliarFullPressure = []
    smiliarStaticPressure = []
    smiliarShaftPower = []
    for flowRate in flowRateData:
        smiliarFlowRate.append(flowRate * math.pow(sdfMs, 1))
    for pressure in fullPressureData:
        # print('pressure')
        # print(pressure)
        temp = pressure * math.pow(sdfMs, 2)
        # print('temp')
        # print(temp)
        smiliarFullPressure.append(temp)
    for pressure in staticPressureData:
        temp = pressure * math.pow(sdfMs, 2)
        smiliarStaticPressure.append(temp)
    for flowRate in shaftPower:
        smiliarShaftPower.append(flowRate * math.pow(sdfMs, 3))
    return {
        'flowRate': smiliarFlowRate,
        'fullPressure': smiliarFullPressure,
        'staticPressure': smiliarStaticPressure,
        'shaftPower': smiliarShaftPower,
    }


def fit_line(xList: list, yList: list, x: float = None):

    an = np.polyfit(xList, yList, 2)
    # print(an)

    # ## 计算R方
    # y2 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    # index = 0
    # for i in x:
    #     y2[index] = an[0]*i**2+an[1]*i+an[2]
    #     index = index+1
    # print(y2)
    # correlation = np.corrcoef(yData, y2)[0, 1]  # 相关系数
    # r = correlation**2  # R方
    # print('R')
    # print(r)
    if x != None:
        result = an[0]*x*x+an[1]*x+an[2]
        # print('fit result')
        # print(result)
        return math.floor(result)
    else:
        return an


def fit_perf_data(flowRateData: list, pressureData: list, impellerDia: float, originImpellerDia: float,  x: float = None):
    # print('flowRateData')
    # print(flowRateData)
    # print('pressureData')
    # print(pressureData)
    # 计算直径比
    sdfImp = impellerDia / originImpellerDia
    # print('impellerDia')
    # print(impellerDia)
    # print('originImpellerDia')
    # print(originImpellerDia)
    # print('sdfImp')
    # print(sdfImp)
    smiliarFlowRate = []
    smiliarPressure = []
    for flowRate in flowRateData:
        smiliarFlowRate.append(flowRate * math.pow(sdfImp, 3))
    for pressure in pressureData:
        # print('pressure')
        # print(pressure)
        temp = pressure * math.pow(sdfImp, 2)
        # print('temp')
        # print(temp)
        smiliarPressure.append(temp)

    # print('smiliarPressure')
    # print(smiliarPressure)

    # print('x')
    # print(x)
    # 拟合相似设计后的流量与压力的曲线，二次函数
    an = np.polyfit(smiliarFlowRate, smiliarPressure, 2)
    # print(an)

    # ## 计算R方
    # y2 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    # index = 0
    # for i in x:
    #     y2[index] = an[0]*i**2+an[1]*i+an[2]
    #     index = index+1
    # print(y2)
    # correlation = np.corrcoef(yData, y2)[0, 1]  # 相关系数
    # r = correlation**2  # R方
    # print('R')
    # print(r)
    if x != None:
        result = an[0]*x*x+an[1]*x+an[2]
        # print('fit result')
        # print(result)
        return math.floor(result)
    else:
        return an
