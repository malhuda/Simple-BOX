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
from typing import Optional, Tuple, Dict
from urllib.parse import ParseResult, urlparse

from py_fortify.constants import MIME_DICT
from py_fortify.unity import is_blank
from py_fortify.log import logger


# TODO

class BaseParser(object):
    __slots__ = ['full_path_file_string']

    def __init__(self, full_path_file_string: str) -> None:
        self.full_path_file_string = full_path_file_string

        # if is_blank(self.full_path_file_string):
        #     raise ValueError("full path file string is blank")

    @property
    def raw_string(self) -> str:
        return self.full_path_file_string

        # .....

        pass


class FilePathParser(BaseParser):
    # TODO
    def __init__(self, **kwargs) -> None:
        super(FilePathParser, self).__init__(**kwargs)

    @property
    def is_exist(self) -> bool:
        return os.path.exists(self.full_path_file_string)

    @property
    def is_file(self) -> bool:
        return os.path.isfile(self.full_path_file_string)

    @property
    def is_dir(self) -> bool:
        return os.path.isdir(self.full_path_file_string)

    @property
    def driver(self) -> Optional[str]:
        return None if is_blank(os.path.splitdrive(self.full_path_file_string)[0]) else \
            os.path.splitdrive(self.full_path_file_string)[0]

    @property
    def dirname(self) -> Optional[str]:
        return None if is_blank(os.path.dirname(self.full_path_file_string)) else os.path.dirname(
            self.full_path_file_string)

    @property
    def basename(self) -> Optional[str]:
        return None if is_blank(os.path.basename(self.full_path_file_string)) else os.path.basename(
            self.full_path_file_string)

    @property
    def source_name(self) -> Optional[str]:
        return self.basename

    @property
    def source_path(self) -> Optional[str]:
        if self.source_name is None:
            return self.full_path_file_string
        return self.full_path_file_string.replace(self.source_name, "")

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

    # ....


class UrlPathParser(BaseParser):
    # TODO
    def __init__(self, **kwargs):
        super(UrlPathParser, self).__init__(**kwargs)
        self._parsed = urlparse(self.full_path_file_string)

    @property
    def parsed(self) -> ParseResult:
        return self._parsed

    @parsed.setter
    def set_parsed(self, value) -> None:
        self._parsed = value

    @property
    def is_http(self) -> bool:
        return False if not self.full_path_file_string.startswith("http") and \
                        not self.full_path_file_string.startswith("https") else True

    @property
    def scheme(self) -> Optional[str]:
        return self._parsed.scheme

    def fetch_source_from_url(self) -> Optional[str]:
        last_sep = self.full_path_file_string.split("/")[-1]
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
        return self.path.replace("/", "")

    @property
    def source_name(self) -> Optional[str]:
        return None if is_blank(self.source_name_and_suffix) else self.source_name_and_suffix.split(".")[0]

    @property
    def source_suffix(self) -> Optional[str]:
        return None if is_blank(self.source_name_and_suffix) else self.source_name_and_suffix.split(".")[-1]

    @property
    def source_mime(self) -> Optional[str]:
        return None if is_blank(self.source_suffix) else MIME_DICT.get(self.source_suffix)
