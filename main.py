# -*- coding:utf-8 -*-
'''
@Description: 入口函数
@Author: lamborghini1993
@Date: 2019-04-24 17:01:40
@UpdateDate: 2019-04-25 15:14:08
'''


import sys
import os
import logging

from pubcode.pubfunc import pubmisc
from net import server


def InitDir():
    for sDir in ("log",):
        if os.path.exists(sDir):
            continue
        os.makedirs(sDir)


def InitConfig():
    sys.excepthook = pubmisc.SysExceptHook

    sTime = pubmisc.Time2Str(timeformat="%Y-%m-%d")
    sLogName = os.path.join("log", sTime+".log")
    handler = logging.FileHandler(filename=sLogName, mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(filename)s(%(lineno)d) - %(levelname)s - %(message)s"))
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)


def NetStart():
    server.GetServerMgr().Start()


def Main():
    InitDir()
    InitConfig()
    NetStart()


if __name__ == "__main__":
    Main()
