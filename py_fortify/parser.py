# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: parser.py
 Time: 10/27/18

 解析模块
"""
import os
import re
from ntpath import sep as ntsep
from posixpath import sep as posixsep
from typing import Optional, Tuple
from urllib.parse import ParseResult, urlparse

from py_fortify.constants import MIME_DICT
from py_fortify.unity import is_blank, is_not_blank

FILE_DOT = "."


# TODO

class BaseParser(object):
    __slots__ = ['_full_path_file_string']

    def __init__(self, full_path_file_string: str) -> None:
        self._full_path_file_string = full_path_file_string

        if self._full_path_file_string is None:
            raise ValueError("full path file string is None!")

    @property
    def is_blank(self) -> bool:
        return is_blank(self._full_path_file_string)

    @property
    def is_not_blank(self) -> bool:
        return not self.is_blank

    @property
    def full_path_file_string(self) -> str:
        return self._full_path_file_string

    @full_path_file_string.setter
    def full_path_file_string(self, value) -> None:
        assert value is not None
        self._full_path_file_string = value

        # .....

        pass


class FilePathParser(BaseParser):
    # TODO
    def __init__(self, **kwargs) -> None:
        super(FilePathParser, self).__init__(**kwargs)

    @property
    def is_exist(self) -> bool:
        return os.path.exists(self._full_path_file_string)

    @property
    def is_not_exist(self) -> bool:
        return not self.is_exist

    @property
    def is_file(self) -> bool:
        return os.path.isfile(self._full_path_file_string)

    @property
    def is_not_file(self) -> bool:
        return not self.is_file

    @property
    def is_dir(self) -> bool:
        return os.path.isdir(self._full_path_file_string)

    @property
    def is_not_dir(self) -> bool:
        return not self.is_dir

    @property
    def is_windows_file(self) -> bool:
        if ntsep in self.full_path_file_string:
            return True
        else:
            return False

    @property
    def driver(self) -> Optional[str]:
        return None if is_blank(os.path.splitdrive(self._full_path_file_string)[0]) else \
            os.path.splitdrive(self._full_path_file_string)[0]

    @property
    def dirname(self) -> Optional[str]:
        return None if is_blank(os.path.dirname(self._full_path_file_string)) else os.path.dirname(
            self._full_path_file_string)

    @property
    def basename(self) -> Optional[str]:
        return None if is_blank(os.path.basename(self._full_path_file_string)) else os.path.basename(
            self._full_path_file_string)

    @property
    def source_name(self) -> Optional[str]:
        return self.basename

    @property
    def source_name_without_suffix(self) -> Optional[str]:
        return self.source_name.replace(self.source_suffix, "").replace(FILE_DOT, "")

    @property
    def source_path(self) -> Optional[str]:
        if self.is_dir:
            return self._full_path_file_string
        if self.source_name is None:
            return self._full_path_file_string
        return self._full_path_file_string.replace(self.source_name, "")

    @property
    def source_suffix(self) -> Optional[str]:
        return None if self.source_name is None or not self.source_name.__contains__(".") else \
            self.source_name.split(".")[-1]

    @property
    def source_mime(self) -> Optional[str]:
        return None if self.source_suffix is None else MIME_DICT.get(self.source_suffix)

    @property
    def source_path_and_name(self) -> Tuple[Optional[str], Optional[str]]:
        return self.source_path, self.source_name

    @property
    def size(self) -> Optional[int]:
        if self.is_exist and self.is_file:
            return os.path.getsize(self.full_path_file_string)
        return None

    def set_source_name(self, excepted_source_name) -> str:
        """
        Set source name which expected
        sample as
        a = FilePathParser(_full_path_file_string = '/foo/bar.jpg')
        b = a.set_source_name(excepted_source_name='cat.jpg')
        # '/foo/cat.jpg'
        :param excepted_source_name:
        :return:
        """
        return os.path.join(self.source_path,
                            excepted_source_name) if self.source_path is not None else excepted_source_name

    def translate_to_linux_file(self):
        if is_blank(self.full_path_file_string):
            return self.full_path_file_string

        if not self.is_windows_file:
            return self.full_path_file_string

        return os.path.join(posixsep, posixsep.join(
            filter(lambda _item: is_not_blank(_item)
                                 and _item != self.driver, self.full_path_file_string.split(ntsep))))

    def translate_to_linux_parser(self):
        return FilePathParser(_full_path_file_string=self.translate_to_linux_file())

    @classmethod
    def files_generator(cls, file_path: str):
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                global roots, dirs
                for roots, dirs, files in os.walk(top=file_path):
                    for _file in files:
                        local_file_path = os.path.join(roots, _file)
                        yield local_file_path

                    if len(dirs) > 0:
                        for _dir in dirs:
                            local_folder_path = os.path.join(roots, _dir)
                            cls.files_generator(file_path=local_folder_path)
            else:
                yield file_path
        else:
            yield None


class UrlPathParser(BaseParser):
    # TODO
    def __init__(self, **kwargs):
        super(UrlPathParser, self).__init__(**kwargs)
        self._parsed = urlparse(self._full_path_file_string)

    @property
    def parsed(self) -> ParseResult:
        return self._parsed

    @property
    def is_http(self) -> bool:
        return False if not self._full_path_file_string.startswith("http") and \
                        not self._full_path_file_string.startswith("https") else True

    @property
    def is_not_http(self) -> bool:
        return not self.is_http

    @property
    def scheme(self) -> Optional[str]:
        return self._parsed.scheme

    def fetch_source_from_url(self) -> Optional[str]:
        last_sep = self._full_path_file_string.split("/")[-1]
        if last_sep.__contains__("?"):
            return re.findall(r'^(.+?)\?', last_sep)[0]
        elif last_sep.__contains__(":"):
            return re.findall(r'^(.+?):', last_sep)[0]
        return last_sep

    @property
    def path(self) -> Optional[str]:
        if self._parsed.path is not None:
            return self._parsed.path
        return self.fetch_source_from_url()

    @property
    def params(self) -> Optional[str]:
        return self._parsed.params

    @property
    def query(self) -> Optional[str]:
        return self._parsed.query

    @property
    def query_map(self) -> Optional[dict]:
        if is_blank(self.query):
            return None
        _ = {}
        for single_mapping_item in self.query.split("&"):
            single_mapping_item = single_mapping_item.strip().replace("\t", "").replace("\n", "")
            if '=' not in single_mapping_item:
                continue
            kv_list = single_mapping_item.split('=')
            if len(kv_list) == 0:
                continue
            _[kv_list[0]] = kv_list[1]
        return _

    @property
    def fragment(self) -> Optional[str]:
        return self._parsed.fragment

    @property
    def username(self) -> Optional[str]:
        return self._parsed.username

    @property
    def password(self) -> Optional[str]:
        return self._parsed.password

    @property
    def hostname(self) -> Optional[str]:
        return self._parsed.hostname

    @property
    def port(self) -> Optional[str]:
        return self._parsed.port

    @property
    def source_name_and_suffix(self) -> Optional[str]:
        if self.path is None:
            return None
        return self.path.split(os.path.sep)[-1]

    @property
    def source_name(self) -> Optional[str]:
        return None if is_blank(self.source_name_and_suffix) else self.source_name_and_suffix.split(".")[0]

    @property
    def source_suffix(self) -> Optional[str]:
        if not self.source_name_and_suffix.__contains__(FILE_DOT):
            return None
        return None if is_blank(self.source_name_and_suffix) else self.source_name_and_suffix.split(".")[-1]

    @property
    def source_mime(self) -> Optional[str]:
        return None if is_blank(self.source_suffix) else MIME_DICT.get(self.source_suffix)
