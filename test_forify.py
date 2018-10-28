# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: test_forify.py
 Time: 10/28/18
"""
import logging
import sys
import os
import ntpath
import posixpath
import unittest
import requests
from py_fortify import UrlPathParser

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logger.setLevel(level)


class TestParser(unittest.TestCase):
    def test_baseparser(self):
        pass

    def test_urlparser(self):
        url = 'https://foo.com/bar.jpg?parms1=1&params2=2#fake'
        u = UrlPathParser(full_path_file_string=url)
        print(u)

    def test_ospath(self):
        path = "C:\\foo\\bar"
        a = os.path.splitdrive(path)
        print(a)

    pass


if __name__ == '__main__':
    unittest.main()
