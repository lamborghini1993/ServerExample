# -*- coding:utf-8 -*-
'''
@Description: 测试socket性能
@Author: lamborghini1993
@Date: 2019-04-25 16:00:45
@UpdateDate: 2019-04-26 11:42:39
'''

import threading
import struct
import marshal
import time
import socket
import random


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


class CSocket(threading.Thread):
    m_MaxBuff = 2048

    def __init__(self, user: str):
        super().__init__()
        self.setDaemon(False)
        self.m_User = user
        self.m_IP = "127.0.0.1"
        self.m_Port = 3163
        self.m_Data = b""
        self.m_Socket = socket.socket()
        self.m_Num = 0
        self.start()

    def run(self):
        self.m_Socket.connect((self.m_IP, self.m_Port))
        self.Login()
        while self.m_Num < 100:
            data = self.m_Socket.recv(self.m_MaxBuff)
            self.MyRecv(data)
        print("%s done" % self.m_User)

    def MyRecv(self, data):
        self.m_Data += data
        while len(self.m_Data) > 4:
            sSize = self.m_Data[:4]
            iSize = struct.unpack("i", sSize)[0]
            if iSize > len(self.m_Data):
                break
            pakage = self.m_Data[:iSize]
            self.m_Data = self.m_Data[iSize:]
            dData = _Deserialization(pakage)
            # print("recv:", dData)
            self.Reply()

    def Login(self):
        data = {
            "user": self.m_User,
            "passwd": "love",
        }
        sData = _Serialization(data)
        self.m_Socket.send(sData)

    def Reply(self):
        self.m_Num += 1
        data = {"num": self.m_Num}
        sData = _Serialization(data)
        time.sleep(random.random())
        self.m_Socket.send(sData)
        # print("send", data)


if __name__ == "__main__":
    # CSocket(123)
    for x in range(1000, 1020):
        CSocket(x)
