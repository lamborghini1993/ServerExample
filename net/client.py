# -*- coding:utf-8 -*-
'''
@Description: 客户端套接字管理
@Author: lamborghini1993
@Date: 2019-04-25 11:25:55
@UpdateDate: 2019-04-25 11:31:35
'''


g_ClientMgr = None


class CClientMgr:
    def NewClient(self, fileno:int, ip:str, port:int):
        pass


def GetClientMgr()->CClientMgr:
    global g_ClientMgr
    if not g_ClientMgr:
        g_ClientMgr = CClientMgr()
    return g_ClientMgr
