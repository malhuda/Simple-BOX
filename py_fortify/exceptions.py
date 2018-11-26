# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://iliangqunru.bitcron.com/
 File: exceptions
 Time: 2018/11/20
 
 Add New Functional exceptions
"""


class PyForifyBaseException(Exception):
    __slots__ = ['message']

    def __init__(self, message: str) -> None:
        self.message = message


class PyForifyDownloaderException(PyForifyBaseException):
    def __init__(self, message) -> None:
        self.message = message
