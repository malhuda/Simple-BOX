# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: unity.py
 Time: 10/27/18
 常用方法
"""


def is_blank(pstr: str) -> bool:
    return True if pstr is None or pstr.strip('') == '' else False


def is_not_blank(pstr: str) -> bool:
    return not is_blank(pstr=pstr)
