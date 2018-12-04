# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: __init__.py.py
 Time: 10/27/18

 py_fortify  python 通用工具封装，遵循PEP8

 注：fortify 增强

"""
import sys
from .parser import UrlPathParser, FilePathParser
from .unity import *

try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor > 5
except Exception as ex:
    raise AssertionError("pyfortify only support 3.6+ !")
