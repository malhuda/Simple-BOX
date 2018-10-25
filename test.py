# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: test.py
 Time: 10/26/18
"""

import unittest

from dropbox_api.dropbox_api import *


class TestSingleMethod(unittest.TestCase):
    """
    test single method
    """

    def test_separate_path_and_name(self):
        path_and_name = "/foo/bar/cat.jpg"
        path, name = separate_path_and_name(path_and_name)
        assert path == '/foo/bar/'
        assert name == 'cat.jpg'

        path_and_name = "/foo/bar/"
        path, name = separate_path_and_name(path_and_name)
        assert path == '/foo/bar/'
        assert name == ''

        path_and_name = "foo/bar"
        path, name = separate_path_and_name(path_and_name)
        assert path == '/foo/'
        assert name == 'bar'

    def test_fetch_filename_from_url(self):
        url = "http://foo.com/bar.jpg"
        file_name = fetch_filename_from_url(url=url)
        assert file_name == 'bar.jpg'

        url = "http://foo.com/bar"
        file_name = fetch_filename_from_url(url=url)
        assert file_name == 'bar'

        url = "http://foo.com/bar.jpg?params=1"
        file_name = fetch_filename_from_url(url=url)
        assert file_name == 'bar.jpg'

    def test_queue_pool(self):
        queue_pool.put_nowait(1)
        queue_pool.put_nowait(2)
        queue_pool.put_nowait(3)
        queue_pool.put_nowait(4)
        queue_pool.put_nowait(5)
        queue_pool.put_nowait(6)
        queue_pool.put_nowait(7)
        queue_pool.put_nowait(8)
        queue_pool.put_nowait(9)
        queue_pool.put_nowait(10)
        assert queue_pool.full() == True


if __name__ == '__main__':
    unittest.main()
