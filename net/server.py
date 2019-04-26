# -*- coding:utf-8 -*-
'''
@Description: 服务端socket通信
@Author: lamborghini1993
@Date: 2019-04-24 17:03:31
@UpdateDate: 2019-04-26 11:28:44
'''

import logging
import select
import socket
import time
import struct
import marshal
import platform

from .client import GetClientMgr


g_ServerMgr = None


def _Serialization(data: dict)->bytes:
    """序列化"""
    sData = marshal.dumps(data)
    size = len(sData) + 4
    sSize = struct.pack("i", size)
    result = sSize + sData
    return result


def _Deserialization(data: bytes)->dict:
    """反序列化"""
    data = data[4:]
    result = marshal.loads(data)
    return result


class CBaseServer:
    m_MaxBuff = 2048

    def __init__(self):
        self.m_Close = False
        self.m_Server = None    # 服务端套接字
        self.m_SocketList = []  # 套接字列表
        self.m_SocketInfo = {}  # fileno:socket
        self.m_RecvBuff = {}    # fileno:data
        self.m_SendBuff = {}    # fileno:data

        self.m_Fileno2User = {}  # id:fileno
        self.m_FilenoNum = {}       #

    def _InitServer(self):
        """初始化服务器套接字"""
        self.m_Server = socket.socket()
        # SO_REUSEADDR，操作系统会在服务器socket被关闭之后马上释放该端口（一般情况下操作系统）
        self.m_Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_Server.setblocking(False)
        self.m_Server.bind(("0.0.0.0", 3163))
        self.m_Server.listen(1)
        self.m_SocketList.append(self.m_Server)
        self.m_SocketInfo[self.m_Server.fileno()] = self.m_Server

    def Start(self):
        self._InitServer()

    def CloseClient(self, fileno: int, reason: str = ""):
        tt = self.m_Fileno2User.get(fileno, fileno)
        num = self.m_FilenoNum.get(fileno, 0)
        logging.warning("%s close,%s num,reason:%s" % (tt, num, reason))
        if fileno not in self.m_SocketInfo:
            return
        conn = self.m_SocketInfo[fileno]
        if conn in self.m_SocketList:
            self.m_SocketList.remove(conn)
        if fileno in self.m_RecvBuff:
            del self.m_RecvBuff[fileno]
        if fileno in self.m_SendBuff:
            del self.m_SendBuff[fileno]
        try:
            conn.close()
        except:
            pass

    def CloseAllSocket(self, reason=""):
        logging.info("close all socket:%s" % reason)
        self.m_Close = True
        for conn in self.m_SocketList:
            try:
                conn.close()
            except:
                pass
        self.m_SocketList = []
        self.m_SocketInfo = {}
        self.m_RecvBuff = {}
        self.m_SendBuff = {}

    def AcceptClient(self)->int:
        try:
            conn, tAddr = self.m_Server.accept()
        except Exception as e:
            self.CloseAllSocket(str(e))
            return 0
        fileno = conn.fileno()
        conn.setblocking(False)
        self.m_SocketList.append(conn)
        self.m_SocketInfo[fileno] = conn
        ip, port = tAddr
        GetClientMgr().NewClient(fileno, ip, port)
        return fileno

    def SocketSend(self, fileno: int):
        conn = self.m_SocketInfo[fileno]
        data = self.m_SendBuff.get(fileno, b"")
        while data:
            conn.send(data[:self.m_MaxBuff])

            # try:
            #     conn.send(data[:self.m_MaxBuff])
            # except:
            #     self.CloseClient(fileno, "send error")
            #     return
            data = data[self.m_MaxBuff:]
        self.m_SendBuff[fileno] = b""

    def SocketRecv(self, fileno: int):
        conn = self.m_SocketInfo[fileno]
        try:
            data = conn.recv(self.m_MaxBuff)
            if not data:
                self.CloseClient(fileno, "recv none")
                return
        except Exception as e:
            self.CloseClient(fileno, "recv error:%s" % e)
            return
        sRecvData = self.m_RecvBuff.setdefault(fileno, b"")
        sRecvData += data
        while True:
            iLen = len(sRecvData)
            if iLen < 4:
                return
            sSize = sRecvData[:4]
            iSize = struct.unpack("i", sSize)[0]
            if iSize > iLen:
                break
            sPackage = sRecvData[:iSize]
            sRecvData = sRecvData[iSize:]
            try:
                dData = _Deserialization(sPackage)
                # print("recv(%s) %s" % (fileno, dData))
            except:
                self.CloseClient(fileno, "_Deserialization error")
                return
            self.Command(fileno, dData)
        self.m_RecvBuff[fileno] = sRecvData

    def Send(self, fileno: int, data: dict):
        sData = _Serialization(data)
        if fileno not in self.m_SendBuff:
            self.m_SendBuff[fileno] = b""
        self.m_SendBuff[fileno] += sData

    def Command(self, fileno: int, dData: dict):
        """解析协议"""
        from pubcode.pubfunc import pubmisc
        if "user" in dData:
            user = dData["user"]
            self.m_Fileno2User[fileno] = user
            # self.m_UserLogger[fileno] = pubmisc.SetLogger(str(user), "log/%s.log" % user)
            self.Send(fileno, {"user": True})
            return
        # logger = self.m_UserLogger[fileno]
        user = self.m_Fileno2User[fileno]
        num = dData["num"]
        self.m_FilenoNum[fileno] = num
        # logging.debug("%s %s" % (user, num))
        dReply = {"reply": num}
        self.Send(fileno, dReply)


class CEpollServer(CBaseServer):
    """"
    epoll服务
    """

    def __init__(self):
        super().__init__()
        self.m_Epoll = None

    def _InitServer(self):
        super()._InitServer()
        self.m_Epoll = select.epoll()
        self.m_Epoll.register(self.m_Server.fileno(), select.EPOLLIN)

    def Start(self):
        super().Start()
        logging.info("epoll wait...")
        while True:
            if self.m_Close:
                return
            events = self.m_Epoll.poll(1)
            if not events:
                time.sleep(0.2)
                continue
            for fileno, event in events:
                if fileno == self.m_Server.fileno():
                    cfileno = self.AcceptClient()
                    self.m_Epoll.register(cfileno, select.EPOLLIN | select.EPOLLOUT)
                elif event & select.EPOLLIN:
                    self.SocketRecv(fileno)
                elif event & select.EPOLLOUT:
                    self.SocketSend(fileno)
                else:
                    self.CloseClient(fileno, "epoll error")

    def CloseClient(self, fileno: int, reason: str = ""):
        super().CloseClient(fileno, reason)
        self.m_Epoll.unregister(fileno)


def GetServerMgr()->CEpollServer:
    global g_ServerMgr
    if not g_ServerMgr:
        if platform.system() == "Linux":
            g_ServerMgr = CEpollServer()
    return g_ServerMgr
