# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: unity.py
 Time: 10/27/18
 常用方法
"""
from contextlib import contextmanager
from typing import Optional

from py_fortify.constants import MIME_DICT


@contextmanager
def open_file(file_name: str, mode: str = 'wb'):
    file = open(file=file_name, mode=mode)
    yield file
    file.flush()
    file.close()


def is_blank(pstr: str) -> bool:
    return True if pstr is None or pstr.strip('') == '' else False


def is_not_blank(pstr: str) -> bool:
    return not is_blank(pstr=pstr)


def get_mime(suffix: str) -> Optional[str]:
    return MIME_DICT.get(suffix)


def get_suffix(mime: str) -> Optional[str]:
    for k, v in MIME_DICT.items():
        if v == mime:
            return k
    return None


def assert_state(state: bool, message: str) -> None:
    if not state:
        raise Exception(message)
