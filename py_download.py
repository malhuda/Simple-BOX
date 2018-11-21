# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://iliangqunru.bitcron.com/
 File: py_download
 Time: 2018/11/19
 
 Add New Functional py_download
"""
import logging
import sys
import io
import threading
from typing import Tuple, IO, Any
from contextlib import contextmanager

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
PY3 = False

if sys.version > '3':
    PY3 = True

import math
import requests


@contextmanager
def open_file(file_name: str, mode: str = "wb"):
    file = open(file=file_name, mode=mode)
    yield file
    file.flush()
    file.close()


fw = open(file="google.png", mode="wb")

download_url = 'https://imgsrc.baidu.com/baike/pic/item/a8014c086e061d954d0dcf4a77f40ad162d9ca7d.jpg'


def download_with_raneg(byte_range: Tuple[int, int], url: str, f: IO[Any]):
    try:
        start = byte_range[0]
        end = byte_range[1]
        print("> 开始下载段, %s —— %s" % (start, end))
        headers = {'Range': 'Bytes=%s-%s' % (start, end), 'Accept-Encoding': '*'}
        res = requests.get(url=url, headers=headers, stream=True)

        # if res.status_code != 200:
        #     print(res.content)
        #     return

        f.seek(start)
        f.write(res.content)
        f.flush()
        # buffer = io.BytesIO()
        # for chunk in res.iter_content(chunk_size=1*1024):
        #     if chunk:
        #         buffer.write(chunk)
        #         buffer.flush()
        #     else:
        #         break
        # fw.write(buffer.getvalue())
        # fw.flush()
        # if not buffer.closed:
        #     buffer.close()

    except Exception as ex:
        print(ex)


thread_count = 5
r = requests.head(
    url=download_url)
content_length = r.headers.get("Content-Length")
print("> 下载文件大小, %s" % content_length)

offset = math.floor((int(content_length) / thread_count))

slice_list = []
for i in range(thread_count):

    if i == thread_count - 1:
        slice_list.append((i * offset, content_length))
    else:
        start, end = i * offset, (i + 1) * offset
        slice_list.append((start, end))

for single_slice in slice_list:
    t = threading.Thread(target=download_with_raneg, args=(single_slice,
                                                           download_url,
                                                           fw))
    t.start()

