# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: unity.py
 Time: 10/27/18
 常用方法
"""
__all__ = ['open_file', 'is_blank', 'is_not_blank', 'get_mime', 'get_suffix', 'assert_state', 'equal_ignore',
           'AtomicInt']
import threading
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
    if state:
        raise Exception(message)


def equal_ignore(foo: str, bar: str) -> bool:
    if foo is None and bar is None: return True
    if foo is None: return False
    if bar is None: return False
    return foo.strip().lower() == bar.strip().lower()


class AtomicInt:
    __slots__ = ['_current_thread', '_value', '_lock']

    def __init__(self, value=0) -> None:
        self._value = value
        self._lock = threading.Lock()
        self._current_thread = threading.current_thread()

    @property
    def get(self):
        with self._lock:
            return self._value

    @get.setter
    def set(self, value):
        with self._lock:
            self._value = value

    def get_and_increment(self):
        with self._lock:
            self._value += 1

    def get_and_decrement(self):
        with self._lock:
            self._value += -1


def show_flag(i):
    print(i)


if __name__ == '__main__':
    a = AtomicInt(value=10000)
    while True:
        a.get_and_decrement()
        t = threading.Thread(target=show_flag, args=(a.get,))
        t.start()
