# -*- coding:utf-8 -*-
'''
@Description: 入口函数
@Author: lamborghini1993
@Date: 2019-04-24 17:01:40
@UpdateDate: 2019-04-26 11:01:52
'''


import sys
import os

from pubcode.pubfunc import pubmisc
from net import server


def InitDir():
    for sDir in ("log",):
        if os.path.exists(sDir):
            continue
        os.makedirs(sDir)


def InitConfig():
    sys.excepthook = pubmisc.SysExceptHook

    sLogName = os.path.join("log", "love.log")
    pubmisc.SetLogger("", sLogName, format="%(asctime)s - %(filename)s(%(lineno)d) - %(levelname)s - %(message)s")


def NetStart():
    server.GetServerMgr().Start()


def Main():
    InitDir()
    InitConfig()
    NetStart()


if __name__ == "__main__":
    Main()
