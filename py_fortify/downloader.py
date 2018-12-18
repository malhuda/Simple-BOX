# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://iliangqunru.bitcron.com/
 File: downloader
 Time: 2018/11/20
 
 Add New Functional downloader
"""

import math
import os
import threading
from typing import Tuple

import requests

from py_fortify import UrlPathParser, FilePathParser, is_blank
from py_fortify.exceptions import PyForifyDownloaderException
from concurrent.futures import ThreadPoolExecutor

ZERO_SIZE = 0
D_POOL = ThreadPoolExecutor(10)


class Downloader(object):
    __slots__ = ['url', 'local_file_path', 'file', 'thread_count', 'slice_list', 'bts']

    def __init__(self, url, local_file_path, **kwargs):
        self.url = url
        self.local_file_path = local_file_path or os.getcwd()
        self.thread_count = kwargs.get("thread_count") or 1
        self.bts = []

        _lfpp = FilePathParser(full_path_file_string=self.local_file_path)
        if _lfpp.is_blank:
            raise PyForifyDownloaderException(message="local file path is blank !")

        # TODO check lfpp

        _urlpp = UrlPathParser(full_path_file_string=self.url)
        if _urlpp.is_blank:
            raise PyForifyDownloaderException(message="url is blank !")
        if _urlpp.is_not_http:
            raise PyForifyDownloaderException(message="url protocol not support http !")

        self.file = open(file=self.local_file_path, mode='wb')

    def get_total_size(self, **request_params) -> int:
        rh = requests.head(self.url, **request_params)
        return ZERO_SIZE if is_blank(rh.headers.get("Content-Length")) else rh.headers.get("Content-Length")

    def get_slice_list(self, **kwargs):
        total_size = self.get_total_size(**kwargs)
        _slice_list = []
        if self.get_total_size() != ZERO_SIZE:
            offset = math.floor((int(total_size) / self.thread_count))

            for i in range(self.thread_count):
                if i == self.thread_count - 1:
                    _slice_list.append((i * offset, total_size))
                else:
                    start, end = i * offset, (i + 1) * offset
                    _slice_list.append((start, end))

        return _slice_list

    def _download_with_range(self, byte_range: Tuple[int, int], segment_flag: int):

        _start = byte_range[0]
        _end = byte_range[1]
        _headers = {'Range': 'Bytes=%s-%s' % (_start, _end), 'Accept-Encoding': '*'}
        _rs = requests.get(url=self.url, headers=_headers, stream=True)

        # TODO
        # for _buffer in _rs.iter_content(chunk_size=10):
        #     self.file.seek(_start)

        # self.bts.insert(segment_flag, _rs.content)
        self.file.seek(_start)
        self.file.write(_rs.content)
        self.file.flush()
        print("> 段 %s, %s —— %s , 写入成功!" % (segment_flag, _start, _end))

        if segment_flag == self.thread_count:
            print("> 写入完成")

    def run(self):
        flag = 0
        for _single_slice in self.get_slice_list():
            t = D_POOL.submit(self._download_with_range, _single_slice, flag)
            flag += 1

if __name__ == '__main__':
    d = Downloader(url='http://file.allitebooks.com/20160611/Kali%20Linux%20Web%20Penetration%20Testing%20Cookbook.pdf',
                   thread_count=5,
                   local_file_path=r"D:\open_code\Simple-BOX\Simple-BOX\da.pdf")
    d.run()
