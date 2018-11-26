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
from py_fortify import UrlPathParser, FilePathParser, equal_ignore, assert_state, PyForifyBaseException
from py_fortify.constants import MIME_DICT
from dropbox_api.dropbox_api import separate_path_and_name

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

        url = 'https://desolate-ravine-49980.herokuapp.com/static/de'
        u = UrlPathParser(full_path_file_string=url)
        assert u.source_name_and_suffix == 'de'
        print(u)

    def test_ospath(self):
        path = "C:\\foo\\bar"
        a = os.path.splitdrive(path)
        print(a)

    def test_fileparser(self):
        file_name_path = "/foo/bar/1.jpg"
        a = FilePathParser(full_path_file_string=file_name_path)
        assert a.source_name == '1.jpg'
        assert a.source_path == '/foo/bar/'
        assert a.source_suffix == 'jpg'
        assert a.source_mime == MIME_DICT.get(a.source_suffix)

        file_name_path = "/foo/bar/1"
        a = FilePathParser(full_path_file_string=file_name_path)
        assert a.source_name == '1'
        assert a.source_path == '/foo/bar/'
        assert a.source_suffix is None

        print("======")
        path, name = separate_path_and_name(file_name_path)
        print(path, name)
        path2, name2 = a.source_path_and_name
        print(path2, name2)

    def test_equal_ignore(self):
        foo = "aaaa"
        bar = "aaaa   "
        r = equal_ignore(foo, bar)
        print(r)

    def test_translate_windows_file_to_linux(self):
        path = "C:\\foo\\bar\\cat.jpg"
        a = FilePathParser(full_path_file_string=path)
        b = a.translate_to_linux_file()
        print(b)

    def test_exceptions(self):
        try:
            assert_state(False, "测试PyForifyException", )
        except Exception as ex:
            print(ex)
        pass


if __name__ == '__main__':
    unittest.main()
