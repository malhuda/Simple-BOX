# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: dropbox_api.py
 Time: 10/4/18
"""
from __future__ import print_function
import asyncio
import io
import logging
import os
import sys
from typing import List, Optional, Tuple

import dropbox
import requests
from dropbox.files import FileMetadata, ListFolderResult
from flask import flash, request, redirect, render_template
from werkzeug.utils import secure_filename

from py_fortify import is_not_blank, is_blank, open_file, FilePathParser, UrlPathParser, get_suffix
from py_fortify.parser import BaseParser

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logger.setLevel(level)

ACCESS_TOKEN = 'i8G-xobvWUQAAAAAAAABAAzg8_EbfSdZJIGzH93kXBoBGloa7jJuHEUJ167U34eC'

FILE_SEP = "/"
FILE_DOT = "."

DROPBOX_FILE_SEP = "/"
DROPBOX_FILE_DOT = "."

_FILEMETADATA_LIST_TYPE = List[FileMetadata]
_FILEMETADATA_TYPE = FileMetadata
_BOOLEAN_TYPE = bool
_DICT_TYPE = dict
_STR_TYPE = str
_OPTION_STR = Optional[_STR_TYPE]

LOOP = asyncio.get_event_loop()

try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor > 5
except Exception as ex:
    raise AssertionError("dropbox-api only support 3.6+.")


def is_debug():
    return logger.level == logging.DEBUG


# ......

#  ==>>> single common methods

class DropboxAPIException(Exception):
    def __init__(self, message) -> None:
        self.message = message


class SimpleAPIException(Exception):
    def __init__(self, message) -> None:
        self.message = message


def separate_path_and_name(file_path: str):
    # if is_blank(file_path):
    #     return None, None
    # fps = file_path.split(FILE_SEP)
    # f_name = fps[-1]
    # f_path = '/'
    # for it in fps[0:-1]:
    #     f_path = os.path.join(f_path, it)
    # f_path = f_path + "/"
    # return f_path, f_name
    return FilePathParser(full_path_file_string=file_path).source_path_and_name


def fetch_filename_from_url(url: str) -> str:
    # if is_blank(url):
    #     return ""
    # last_sep = url.split("/")[-1]
    # if last_sep.__contains__("?"):
    #     return re.findall(r'^(.+?)\?', last_sep)[0]
    # elif last_sep.__contains__(":"):
    #     return re.findall(r'^(.+?):', last_sep)[0]
    # return last_sep
    url_parser = UrlPathParser(full_path_file_string=url)
    return "" if url_parser.source_name_and_suffix is None else url_parser.source_name_and_suffix


def get_mime(file_suffix: str) -> Optional[str]:
    if file_suffix is None:
        raise DropboxAPIException("file suffix is None !")
    if file_suffix.startswith("."):
        file_suffix = file_suffix.replace(".", "")
    mime_dict = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpg",
        "png": "image/png",
        "csv": "text/csv",
        "pdf": "application/pdf",
        "html": "text/html",
        "txt": "text/txt",
        # ....
    }
    return mime_dict.get(file_suffix)


def response_wrapper(func):
    def wrapper(*args, **kwargs):
        ret_wrapper = {'success': False, 'request': [], 'response': None, 'exception': None}

        if kwargs is not None and kwargs.__len__() > 0:
            ret_wrapper['request'].append(str(kwargs))
        elif args is not None and args.__len__() > 0:
            ret_wrapper['request'].append(str(args))
        try:
            ret = func(*args, **kwargs)
            ret_wrapper['response'] = ret
            ret_wrapper['success'] = True
        except Exception as ex:
            ret_wrapper['exception'] = str(ex)
        return ret_wrapper

    return wrapper


# ==>>>> Some class


class SimpleFileMetadata(object):
    __slots__ = ['dropbox_file_metadata']

    def __init__(self, dropbox_file_metadata: FileMetadata):
        self.dropbox_file_metadata = dropbox_file_metadata

    @property
    def id(self):
        return self.dropbox_file_metadata.id

    @property
    def name(self):
        return self.dropbox_file_metadata.name

    @property
    def path(self):
        return self.dropbox_file_metadata.path_display

    @property
    def time(self):
        return self.dropbox_file_metadata.server_modified \
            if hasattr(self.dropbox_file_metadata, 'server_modified') else ""

    @property
    def type(self):
        return "file" if self.time != '' and self.__hash__() != '' else "folder"

    def __hash__(self):
        return self.dropbox_file_metadata.content_hash if hasattr(self.dropbox_file_metadata, 'content_hash') else ""

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'path': self.path, 'time': self.time, 'type': self.type,
                'hash': self.__hash__()}

    def __repr__(self):
        return str(self.to_dict())


class SimpleAPI(object):
    __slots__ = ['option_map', 'loop', ]

    def __init__(self, *args, **kwargs):
        # just ext data
        self.option_map = {}
        self.loop = self.option_map.get('loop', asyncio.get_event_loop())

    def upload(self,
               local_file_path: str,
               remote_file_path: str):

        # just invalid path
        if is_blank(remote_file_path):
            raise SimpleAPIException(message="SimpleAPI#upload remote_file_path is blank!")

        __local_file_path_parser = FilePathParser(full_path_file_string=local_file_path)

        if __local_file_path_parser.is_blank:
            raise SimpleAPIException(message="SimpleAPI#upload local_file_path is blank!")

        if __local_file_path_parser.is_not_exist:
            raise SimpleAPIException(message="SimpleAPI#upload local_file_path is not exist !")

        pass

    def download(self,
                 local_file_path: str,
                 remote_file_path: str):
        # just invalid path
        if is_blank(remote_file_path):
            raise SimpleAPIException(message="SimpleAPI#download remote_file_path is blank!")

        __local_file_path_parser = FilePathParser(full_path_file_string=local_file_path)

        if __local_file_path_parser.is_blank:
            raise SimpleAPIException(message="SimpleAPI#download local_file_path is blank!")

        if __local_file_path_parser.is_not_exist:
            raise SimpleAPIException(message="SimpleAPI#download local_file_path is not exist !")

        pass


class SimpleDropboxAPIV2(SimpleAPI):
    """ Simple Dropbox API , `access_token` is dropbox token"""
    __slots__ = ['access_token', 'dbxa', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_token = kwargs.get("access_token")
        self.dbxa = None

    def dbx(self) -> None:
        # dropbox.create_session(proxies={
        #     'http': 'socks5://127.0.0.1:1081',
        #     'https': 'socks5://127.0.0.1:1081'
        # })
        dbx = dropbox.Dropbox(self.access_token)
        if dbx is None:
            raise DropboxAPIException("SimpleDropboxAPI#dbx dbx is None!")
        self.dbxa = dbx

    def upload_to_dropbox(self,
                          file_bytes: bytes,
                          remote_file_path) -> _FILEMETADATA_TYPE:
        """
        invoke dropbox api from bytes
        :param file_bytes:          file bytes which  upload    not blank
        :param remote_file_path:    remote file path            strict rule , sample as `/foo/bar.jpg`
        :return:
        """
        if file_bytes is None:
            raise DropboxAPIException("SimpleDropboxAPI#upload_to_dropbox , bytes is blank!")

        if is_blank(remote_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#upload_to_dropbox , remote file path is blank!")

        if not remote_file_path.startswith(DROPBOX_FILE_SEP):
            raise DropboxAPIException("SimpleDropboxAPI#upload_to_dropbox , remote file path must start with  `/` !")

        if remote_file_path.endswith(DROPBOX_FILE_SEP):
            raise DropboxAPIException("SimpleDropboxAPI#upload_to_dropbox , remote file path must have source name !")

        if is_debug():
            logger.debug("SimpleDropboxAPI#upload_to_dropbox , remote_file_path=%s", remote_file_path)

        if self.dbxa is None:
            self.dbx()
        return self.dbxa.files_upload(file_bytes, remote_file_path, mute=True)

    def async_upload_bytes(self,
                           file_bytes: bytes,
                           remote_file_path: str, ) -> SimpleFileMetadata:
        """
        async upload to dropbox from bytes
        :param file_bytes:          file byte array         not none
        :param remote_file_path     remote file path        strict rule , sample as `/foo/bar.jpg`
        :return:
        """

        async def _async_upload_bytes():
            async def _inner_upload():
                return self.upload_to_dropbox(file_bytes=file_bytes, remote_file_path=remote_file_path)

            return await _inner_upload()

        return SimpleFileMetadata(self.loop.run_until_complete(_async_upload_bytes()))

    def upload_from_local(self,
                          local_file_path: str,
                          remote_file_path: str = None,
                          remote_folder_path: str = None,
                          excepted_name: str = None) -> SimpleFileMetadata:
        """
        upload to dropbox with excepted name

        `excepted_name`       first priority
        `remote_file_path`    second priority
        `remote_folder`       third priority

        :param local_file_path:             file path in local
        :param remote_file_path:            file path in dropbox
        :param remote_folder_path           folder in dropbox
        :param excepted_name:               excepted name which want to rename


        sample as
            >>> self.download_as_file(local_file_path='/foo/bar.jpg',remote_file_path='/DEFAULT/cat.jpg')
            # `/DEFAULT/cat.jpg`
            >>> self.download_as_file(local_file_path='/foo/bar.jpg',remote_file_path='DEFAULT/cat.jpg')
            # `/DEFAULT/cat.jpg`

            >>> self.download_as_file(local_file_path='/foo/bar.jpg',remote_file_path='DEFAULT/cat.jpg',
            >>> excepted_name='dog.jpg')
            # `/DEFAULT/dog.jpg`

            >>> self.download_as_file(local_file_path='/foo/bar.jpg',remote_file_path='DEFAULT/cat.jpg',
            >>> excepted_name='EXCEPTED_DIR/dog.jpg')
            # `/DEFAULT/dog.jpg`
        :return:
        """

        if is_blank(remote_file_path):
            if is_blank(remote_folder_path):
                raise DropboxAPIException(
                    "#upload_with_excepted_name, remote_file_path is blank and remote_folder_path "
                    "is also blank !")

            if not remote_folder_path.startswith(DROPBOX_FILE_SEP):
                remote_folder_path = DROPBOX_FILE_SEP + remote_folder_path
            if not remote_folder_path.endswith(DROPBOX_FILE_SEP):
                remote_folder_path = remote_folder_path + DROPBOX_FILE_SEP
            remote_file_path = remote_folder_path

        if not remote_file_path.startswith(DROPBOX_FILE_SEP):
            remote_file_path = DROPBOX_FILE_SEP + remote_file_path

        lfpp = FilePathParser(full_path_file_string=local_file_path)

        if lfpp.is_blank:
            raise DropboxAPIException("#upload_with_excepted_name, local file path is blank !")

        if lfpp.is_not_exist:
            raise DropboxAPIException("#upload_with_excepted_name, local file path is not exist !")

        if lfpp.is_not_file:
            raise DropboxAPIException("#upload_with_excepted_name, local file path is not a file !")

        rfpp = FilePathParser(full_path_file_string=remote_file_path)
        if is_not_blank(excepted_name):
            # TODO
            if DROPBOX_FILE_SEP in excepted_name:
                remote_file_path = DROPBOX_FILE_SEP + excepted_name if not excepted_name.startswith(DROPBOX_FILE_SEP) else excepted_name
            else:
                remote_file_path = rfpp.set_source_name(excepted_name.split(DROPBOX_FILE_SEP)[-1])

        else:
            remote_file_source = rfpp.source_name
            # case one:
            # remote_file_path  /DEFAULT/A/
            # local_file_path   /foo/bar.jpg
            # auto set          /DEFAULT/A/bar.jpg
            if is_blank(remote_file_source):
                remote_file_path = os.path.join(remote_file_path, lfpp.source_name)

            # case two:
            # remote_file_path  /DEFAULT/A/bar
            # local_file_path   /foo/bar.jpg
            # auto set          /DEFAULT/A/bar.jpg
            elif not remote_file_source.__contains__(DROPBOX_FILE_DOT) and is_not_blank(lfpp.source_suffix):
                remote_file_path = remote_file_path + DROPBOX_FILE_DOT + lfpp.source_suffix

            # case three:
            # remote_file_path  /DEFAULT/A/bar
            # local_file_path   /foo/bar
            # auto set          /DEFAULT/A/bar

        return self.upload(local_file_path=local_file_path, remote_file_path=remote_file_path)

    def upload(self,
               local_file_path: str,
               remote_file_path: str, ) -> SimpleFileMetadata:
        """
        upload to remote file
        :param local_file_path:     local file path which is exist  or throw DropboxException
        :param remote_file_path:    remote file path
        :return:
        """
        super(SimpleDropboxAPIV2, self).upload(local_file_path=local_file_path, remote_file_path=remote_file_path)
        if is_debug():
            logger.debug("SimpleDropboxAPI#upload local_file_path=%s , remote_file_path=%s" % (
                local_file_path, remote_file_path))

        read_buffer = io.BytesIO()

        with open_file(file_name=local_file_path, mode='rb') as lf:
            read_buffer.write(lf.read())

        simple_metadata = self.async_upload_bytes(read_buffer.getvalue(), remote_file_path)

        if is_debug():
            logger.debug("SimpleDropboxAPI#upload metadata=%s" % simple_metadata)
        if not read_buffer.closed:
            read_buffer.close()

        return simple_metadata

    def upload_from_external_url(self,
                                 external_url: str,
                                 remote_file_path: str = None,
                                 remote_folder_path: str = None,
                                 excepted_name: str = None,
                                 **kwargs) -> SimpleFileMetadata:
        """
        upload file which from external url

        in case of all parameters is not none

        `excepted_name`       first priority
        `remote_file_path`    second priority
        `remote_folder`       third priority

        :param external_url:        url from external source
        :param remote_file_path     remote file path
        :param remote_folder_path   remote folder_path
        :param excepted_name        just only excepted name , not with dir path
        :param kwargs:              requests parameters
        :return:
        """
        if is_blank(remote_file_path):
            if is_blank(remote_folder_path):
                raise DropboxAPIException(
                    "#upload_from_external_url, remote_file_path is blank and remote_folder_path "
                    "is also blank !")

            if not remote_folder_path.startswith(DROPBOX_FILE_SEP):
                remote_folder_path = DROPBOX_FILE_SEP + remote_folder_path
            if not remote_folder_path.endswith(DROPBOX_FILE_SEP):
                remote_folder_path = remote_folder_path + DROPBOX_FILE_SEP
            remote_file_path = remote_folder_path

        if not remote_file_path.startswith(DROPBOX_FILE_SEP):
            remote_file_path = DROPBOX_FILE_SEP + remote_file_path

        euup = UrlPathParser(full_path_file_string=external_url)

        if euup.is_blank:
            raise DropboxAPIException("#upload_from_external , upload external url is blank!")
        if euup.is_not_http:
            raise DropboxAPIException("#upload_from_external , upload external url is unknown protocol!")

        rfpp = FilePathParser(full_path_file_string=remote_file_path)

        if is_not_blank(excepted_name):
            # TODO
            if DROPBOX_FILE_SEP in excepted_name:
                excepted_name = DROPBOX_FILE_SEP + excepted_name \
                    if not excepted_name.startswith(DROPBOX_FILE_SEP) else excepted_name
                remote_file_path = excepted_name
            else:
                remote_file_path = rfpp.set_source_name(excepted_name.split(DROPBOX_FILE_SEP)[-1])

        else:
            remote_file_source = rfpp.source_name
            # case one:
            # remote_file_path  /DEFAULT/A/
            # local_file_path   /foo/bar.jpg
            # auto set          /DEFAULT/A/bar.jpg
            if is_blank(remote_file_source):
                remote_file_path = os.path.join(remote_file_path, euup.source_name)
            # case two:
            # remote_file_path  /DEFAULT/A/bar
            # local_file_path   /foo/bar.jpg
            # auto set          /DEFAULT/A/bar.jpg
            elif not remote_file_source.__contains__(DROPBOX_FILE_DOT) and is_not_blank(euup.source_suffix):
                remote_file_path = remote_file_path + DROPBOX_FILE_DOT + euup.source_suffix

            # case three:
            # remote_file_path  /DEFAULT/A/bar
            # local_file_path   /foo/bar
            # auto set          /DEFAULT/A/bar

        if is_debug():
            logger.debug(
                "#upload_from_external_url , remote_file_path=%s, external_url=%s" % (remote_file_path, external_url))

        async def _arequest_external_url():
            async def _inner_request():
                return requests.get(url=external_url, **kwargs, stream=True)

            _res = await _inner_request()
            return _res

        res = self.loop.run_until_complete(_arequest_external_url())
        # Tips: Anti spider policy , 可以把status code 设置非200来迷惑爬虫
        if res.status_code != 200:
            error_msg = "#upload_from_external_url , fail to request ,  url=%s , msg=%s", (external_url, res.txt)
            logger.error(error_msg)
            raise DropboxAPIException(message=error_msg)
        # request success
        content_type = res.headers.get("Content-Type")

        if is_debug():
            logger.info("#upload_from_external_url request <%s> success!" % external_url)

        if DROPBOX_FILE_DOT not in remote_file_path.split(DROPBOX_FILE_SEP)[-1]:
            # get file type (suffix)
            file_suffix = get_suffix(mime=content_type)
            if file_suffix is not None:
                remote_file_path = remote_file_path + DROPBOX_FILE_DOT + file_suffix

        buffer = io.BytesIO()
        for chunk in res.iter_content(chunk_size=20 * 1024):
            if chunk:
                buffer.write(chunk)
            else:
                break

        if is_debug():
            logger.debug("#upload_from_external_url , remote_file_path=%s" % remote_file_path)

        md = self.async_upload_bytes(file_bytes=buffer.getvalue(), remote_file_path=remote_file_path)
        if not buffer.closed:
            buffer.close()
        return md



    def download_from_dropbox(self,
                              remote_file_path: str) -> Tuple[SimpleFileMetadata, bytes]:
        """
        download from dropbox
        :param remote_file_path:        remote file path in dropbox
        :return:                        Tuple[SimpleFileMetadata, bytes]
        """
        if is_blank(remote_file_path):
            raise DropboxAPIException(message="#download_for_bytes , remote file path is blank !")
        rfpp = FilePathParser(full_path_file_string=remote_file_path)
        if not rfpp.source_path.startswith(DROPBOX_FILE_SEP):
            raise DropboxAPIException(message="#download_from_dropbox , remote file path format error!")
        if rfpp.source_name.endswith(DROPBOX_FILE_SEP):
            raise DropboxAPIException(message="#download_from_dropbox , source file name format error !")

        if self.dbxa is None:
            self.dbx()

        metadata, bytes_array = self.dbxa.files_download(remote_file_path)
        return SimpleFileMetadata(metadata), bytes_array

    def async_download_from_dropbox(self,
                                    remote_file_path: str) -> Tuple[SimpleFileMetadata, bytes]:
        """
        async download from dropbox
        :param remote_file_path:        remote file path in dropbox
        :return:                        Tuple[SimpleFileMetadata, bytes]
        """

        async def _download_from_dropbox():
            async def _inner_download():
                return self.download_from_dropbox(remote_file_path=remote_file_path)

            return await _inner_download()

        return self.loop.run_until_complete(_download_from_dropbox())

    def download_as_bytes(self, remote_file_path: str) -> bytes:
        """
        download as bytes
        remote file path is not blank
        :param remote_file_path:        remote file path in dropbox
        :return:                        byte array
        """
        assert is_not_blank(remote_file_path)
        _, file_bytes = self.async_download_from_dropbox(remote_file_path=remote_file_path)
        return file_bytes

    def download_as_file(self,
                         remote_file_path: str,
                         local_file_path: str,
                         excepted_name: str,
                         suffix:str) -> SimpleFileMetadata:
        """
        download as local file
        # if `remote_file_path` not start with `/` , and combine `/` to head;
        # sample as  `foo/bar.jpg` to `/foo/bar.jpg`

        # if source name not in remote file path , throw `DropboxAPIException`
        # if source name not in local file path ,  first fetch excepted name , second fetch local source name
        # sample as
            remote_file_path = "/foo/bar.jpg"       local_path_path="/local/    => "/local/bar.jpg"

        # if excepted name exist , replace source name to excepted name.
        # sample as
            excepted_name = "cat.jpg" ,         local_path_file = "/local/bar.jpg" => "/local/cat.jpg"
            excepted_name = "/animal/cat.jpg" , local_path_file = "/local/bar.jpg" => "/local/cat.jpg"

        usage:
            >>> self.download_as_file(remote_file_path="foo/bar.jpg",local_file_path="/local/bar.jpg",excepted_name="cat.jpg")
            >>> self.download_as_file(remote_file_path="/foo/bar.jpg",local_file_path="/local/bar.jpg",excepted_name="cat.jpg")
            >>> self.download_as_file(remote_file_path="/foo/bar.jpg",local_file_path="/local/bar.jpg",excepted_name="cat.jpg")

        :param remote_file_path:                remote file path and just support single file
        :param local_file_path:                 local file path which download
        :param excepted_name: excepted name     just excepted name which want to rename
        :return:
        """
        if is_blank(remote_file_path):
            raise DropboxAPIException(message="#download_as_file, remote file is blank !")

        if remote_file_path.endswith(DROPBOX_FILE_SEP):
            raise DropboxAPIException(message="#download_as_file, remote file path format error !")

        # if `remote_file_path` not start with `/` , and combine `/` to head;
        # transform `foo/bar.jpg` to `/foo/bar.jpg`
        remote_file_path = remote_file_path if remote_file_path.startswith(
            DROPBOX_FILE_SEP) else DROPBOX_FILE_SEP + remote_file_path

        rfpp = FilePathParser(full_path_file_string=remote_file_path)
        lfpp = FilePathParser(full_path_file_string=local_file_path)

        # if source name not in remote file path , throw `DropboxAPIException`
        if is_not_blank(rfpp.source_name):
            raise DropboxAPIException(message="#download_as_file , remote file path source name is blank !")

        if lfpp.is_blank:
            raise DropboxAPIException(message="#download_as_file , local file path is blank !")

        # if source name not in local file path , throw `DropboxAPIException`
        # if is_blank(lfpp.source_name):
        #     raise DropboxAPIException(message="#download_as_file , local file path source name is blank !")

        # rename local file path . if excepted name exist , replace source name to excepted name.
        #  excepted_name = "cat.jpg" , local_path_file = "/foo/bar.jgp" => "foo/cat.jpg"
        if is_not_blank(excepted_name):
            efpp = FilePathParser(full_path_file_string=excepted_name)
            if is_not_blank(efpp.source_name):
                local_file_path = lfpp.set_source_name(excepted_source_name=excepted_name)
        elif is_blank(lfpp.source_name):
            local_file_path = lfpp.set_source_name(excepted_source_name=rfpp.source_name)

        simple_file_metadata, bytes_array = self.async_download_from_dropbox(remote_file_path=remote_file_path)
        buffer = io.StringIO()
        buffer.write(bytes_array)

        # local file write
        with open_file(file_name=local_file_path,mode="wb") as lwf:
            lwf.write(buffer.getvalue())

        if not buffer.closed():
            buffer.close()
        return simple_file_metadata

    def download(self,
                 *args,
                 **kwargs) -> SimpleFileMetadata:
        """
        download file from dropbox
        :param local_file_path:     local file path which download
        :param remote_file_path:    remote file path which dropbox contain
        :param excepted_name:       excepted name which want to save
        :return:
        """
        return self.download_as_file(*args,**kwargs)
        pass

    def list_from_dropbox(self, remote_folder_path: str) -> ListFolderResult:
        if is_blank(remote_folder_path):
            raise DropboxAPIException(message="#list_from_dropbox , remote folder path is blank !")
        if self.dbxa is None:
            self.dbx()
        return self.dbxa.files_list_folder(remote_folder_path)

    def async_list(self, remote_folder_path: str) -> ListFolderResult:
        async def _async_list():
            async def _inner_list():
                return self.list_from_dropbox(remote_folder_path=remote_folder_path)

            return await _inner_list()

        return self.loop.run_until_complete(_async_list())

    def list(self, remote_folder_path: str) -> ListFolderResult:
        """
        list files in folder
        :param remote_folder_path:
        :return:
        """
        if remote_folder_path is None:
            raise DropboxAPIException("list remote folder path is None")

        while '//' in remote_folder_path:
            remote_folder_path = remote_folder_path.replace('//', '/')
        rf_path, rf_name = separate_path_and_name(remote_folder_path)
        if rf_path is None or rf_path.strip() == '':
            raise DropboxAPIException("list remote folder path is None")

        if self.dbxa is None:
            self.dbx()
        return self.dbxa.files_list_folder(rf_path)

    def download_to_response(self, remote_file_path: str):
        """
        download to response which is from `request`
        :param remote_file_path:
        :return:
        """
        if remote_file_path is None or remote_file_path.strip() == '':
            raise DropboxAPIException("download to bytes remote file path is None")
        rf_path, rf_name = separate_path_and_name(file_path=remote_file_path)
        if rf_name is None or rf_name.strip('') == '':
            raise DropboxAPIException("download to bytes remote file is not exist!")
        if self.dbxa is None:
            self.dbx()
        metadata, response = self.dbxa.files_download(remote_file_path)
        return metadata, response



class SimpleDropboxAPI(object):
    __slots__ = ['access_token', 'dbxa', 'loop']

    def __init__(self, access_token):
        self.access_token = access_token
        self.dbxa = None
        self.loop = asyncio.get_event_loop()

    def dbx(self) -> None:
        dbx = dropbox.Dropbox(self.access_token)
        if dbx is None:
            raise DropboxAPIException("SimpleDropboxAPI#dbx dbx is None!")
        self.dbxa = dbx

    def upload(self,
               local_file_path: str,
               remote_file_path: BaseParser
               ):
        print(local_file_path)
        print(remote_file_path)
        pass

    def upload_with_excepted_name(self,
                                  local_file_path: str,
                                  remote_file_path: str,
                                  excepted_name: str = None) -> _FILEMETADATA_TYPE:
        """
        upload to dropbox
        :param local_file_path:  file path in local
        :param remote_file_path: file path in dropbox
        :param excepted_name:   excepted name which want to rename
        :return:
        """
        if is_blank(local_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#upload local_file_path is blank!")

        if is_blank(local_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#upload remote_file_path is blank!")

        if not os.path.isfile(local_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#upload local_file_path not exist!")

        if is_blank(excepted_name):
            excepted_name = local_file_path.split(FILE_SEP)[-1]

        # not exist file name, sample as `/foo/bar/`, in this case , `remote_file_path` will be set as
        # `/foo/bar`+excepted_name

        # if `remote_file_path` is `/foo/bar` or `/foo/bar.txt` ,then `bar` or `bar.txt` will be excepted_name
        if not remote_file_path.__contains__(FILE_DOT) and is_blank(remote_file_path.split(FILE_SEP)[-1]):
            remote_file_path = os.path.join(remote_file_path, excepted_name)

        if logger.level == logging.DEBUG:
            logger.debug("SimpleDropboxAPI#upload , remote_file_path is %s" % remote_file_path)

        if self.dbxa is None:
            self.dbx()

        with open_file(file_name=local_file_path, mode='rb') as lf:
            metadata = self.dbxa.files_upload(lf.read(), remote_file_path, mute=True)

        if logger.level == logging.DEBUG:
            logger.debug("SimpleDropboxAPI#upload metadata is %s" % metadata)
        return metadata

    # TODO async upload

    @asyncio.coroutine
    def aupload(self,
                local_file_path: str,
                remote_file_path: str,
                excepted_name: str = None) -> _FILEMETADATA_TYPE:
        """
        upload to dropbox
        :param local_file_path:  file path in local
        :param remote_file_path: file path in dropbox
        :param excepted_name:   excepted name which want to rename
        :return:
        """
        if is_blank(local_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#upload local_file_path is blank!")

        if is_blank(local_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#upload remote_file_path is blank!")

        if not os.path.isfile(local_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#upload local_file_path not exist!")

        if is_blank(excepted_name):
            excepted_name = local_file_path.split(FILE_SEP)[-1]

        # not exist file name, sample as `/foo/bar/`, in this case , `remote_file_path` will be set as
        # `/foo/bar`+excepted_name

        # if `remote_file_path` is `/foo/bar` or `/foo/bar.txt` ,then `bar` or `bar.txt` will be excepted_name
        if not remote_file_path.__contains__(FILE_DOT) and is_blank(remote_file_path.split(FILE_SEP)[-1]):
            remote_file_path = os.path.join(remote_file_path, excepted_name)

        if logger.level == logging.DEBUG:
            logger.debug("SimpleDropboxAPI#upload , remote_file_path is %s" % remote_file_path)

        if self.dbxa is None:
            self.dbx()

        with open_file(file_name=local_file_path, mode='rb') as lf:
            metadata = yield from self.dbxa.files_upload(lf.read(), remote_file_path, mute=True)

        return metadata

    def upload_from_bytes(self,
                          file_bytes: bytes,
                          remote_folder_path: str,
                          excepted_name: str) -> SimpleFileMetadata:
        """
        upload to dropbox from bytes
        :param file_bytes:          file byte array
        :param remote_folder_path:  remote folder path
        :param excepted_name:       excepted name
        :return:
        """
        if file_bytes is None:
            raise DropboxAPIException("SimpleDropboxAPI#upload_from_bytes , bytes is blank")

        if remote_folder_path is None or remote_folder_path.strip("") == '':
            raise DropboxAPIException("SimpleDropboxAPI#upload_from_bytes , remote file path is blank!")

        rf_path, rf_name = separate_path_and_name(remote_folder_path)

        if logger.level == logging.DEBUG:
            logger.debug("SimpleDropboxAPI#upload_from_bytes , rf_path is %s , rf_name is %s", (rf_path, rf_name))

        if is_not_blank(excepted_name):
            rf_name = excepted_name

        remote_folder_path = os.path.join(rf_path, rf_name)

        if self.dbxa is None:
            self.dbx()

        md = self.dbxa.files_upload(file_bytes, remote_folder_path, mute=True)
        return SimpleFileMetadata(md)

    def upload_from_external(self, external_url: str, remote_folder_path: str, **kwargs) -> SimpleFileMetadata:
        """
        upload file which from external url
        :param external_url:        url from external source
        :param remote_folder_path:  dropbox folder path
        :param kwargs:
        :return:
        """
        if is_blank(remote_folder_path):
            raise DropboxAPIException("upload remote file path is None!")
        if is_blank(external_url):
            raise DropboxAPIException("upload external url is None!")
        if not external_url.startswith("http"):
            raise DropboxAPIException("upload external url is unknown protocol!")

        timeout = kwargs.get("custom_timeout") or 10
        rf_path, rf_name = separate_path_and_name(remote_folder_path)
        excepted_name = kwargs.get("excepted_name")
        if excepted_name is not None and not excepted_name.strip("") == '':
            rf_name = excepted_name
        else:
            if rf_name is None or rf_name.strip('') == '':
                rf_name = fetch_filename_from_url(external_url)

        if rf_name is None or rf_name.strip('') == '':
            raise DropboxAPIException("upload from external unknown name which is upload")
        remote_folder_path = os.path.join(rf_path, rf_name)

        if kwargs.get('custom_headers') is not None:
            custom_headers = kwargs.get('custom_headers')
            res = requests.get(url=external_url, headers=custom_headers, timeout=timeout, stream=True)
        else:
            res = requests.get(url=external_url, timeout=timeout, stream=True)
        if res.status_code != 200:
            raise DropboxAPIException("upload from external request failed! raw response is %s" % res.text)
        buffer = io.BytesIO()
        for chunk in res.iter_content(chunk_size=20):
            if chunk:
                buffer.write(chunk)
            else:
                break

        if logger.level == logging.DEBUG:
            logger.info("upload from external request <%s> success!" % external_url)
        if self.dbxa is None:
            self.dbx()
        md = self.dbxa.files_upload(buffer.getvalue(), remote_folder_path, mute=True)
        if not buffer.closed:
            buffer.close()
        return SimpleFileMetadata(md)

    def download(self,
                 local_file_path: str,
                 remote_file_path: str,
                 excepted_name: str = None) -> _FILEMETADATA_TYPE:
        """
        download file from dropbox
        :param local_file_path:      local file path which download
        :param remote_file_path:    remote file path which dropbox contain
        :param excepted_name:       excepted name which want to save
        :return:
        """
        if is_blank(pstr=remote_file_path):
            raise DropboxAPIException("SimpleDropboxAPI#download remote_file_path is blank")

        if local_file_path is not None:
            while '//' in local_file_path:
                local_file_path = local_file_path.replace('//', '/')
        if remote_file_path is not None:
            while '//' in remote_file_path:
                remote_file_path = remote_file_path.replace('//', '/')

        rf_path, rf_name = separate_path_and_name(file_path=remote_file_path)
        if rf_name is None or rf_name.strip('') == '':
            raise DropboxAPIException("download remote file is not exist!")
        lf_path, lf_name = separate_path_and_name(file_path=local_file_path)
        if lf_path is not None:
            if not os.path.exists(lf_path):
                os.mkdir(lf_path)
        else:
            lf_path = os.getcwd()

        if excepted_name is not None:
            lf_name = excepted_name
        else:
            if lf_name is None or lf_name.strip("") == '':
                lf_name = rf_name
        local_file_path = os.path.join(lf_path, lf_name)
        if self.dbxa is None:
            self.dbx()
        # metadata, response = self.dbxa.files_download(remote_file_path)
        metadata, response = self.download_to_response(remote_file_path)
        with open_file(file_name=local_file_path, mode='wb') as lf:
            lf.write(response.content)
        return metadata

    def list(self, remote_folder_path: str) -> ListFolderResult:
        """
        list files in folder
        :param remote_folder_path:
        :return:
        """
        if remote_folder_path is None:
            raise DropboxAPIException("list remote folder path is None")

        while '//' in remote_folder_path:
            remote_folder_path = remote_folder_path.replace('//', '/')
        rf_path, rf_name = separate_path_and_name(remote_folder_path)
        if rf_path is None or rf_path.strip() == '':
            raise DropboxAPIException("list remote folder path is None")

        if self.dbxa is None:
            self.dbx()
        return self.dbxa.files_list_folder(rf_path)

    def download_to_response(self, remote_file_path: str):
        """
        download to response which is from `request`
        :param remote_file_path:
        :return:
        """
        if remote_file_path is None or remote_file_path.strip() == '':
            raise DropboxAPIException("download to bytes remote file path is None")
        rf_path, rf_name = separate_path_and_name(file_path=remote_file_path)
        if rf_name is None or rf_name.strip('') == '':
            raise DropboxAPIException("download to bytes remote file is not exist!")
        if self.dbxa is None:
            self.dbx()
        metadata, response = self.dbxa.files_download(remote_file_path)
        return metadata, response


class SimpleDBXServiceAPI(SimpleDropboxAPI):

    # service implement
    def __init__(self, access_token) -> None:
        super().__init__(access_token=access_token)

    def simple_list_entries(self, remote_folder_path: str) -> _FILEMETADATA_LIST_TYPE:
        """
        simple list
        :param remote_folder_path:
        :return:
        """
        return self.list(remote_folder_path=remote_folder_path).entries

    @response_wrapper
    def simple_list(self, remote_folder_path: str) -> List[dict]:
        """
        simple metadata list
        :param remote_folder_path:
        :return:
        """
        return [SimpleFileMetadata(sfm).to_dict() for sfm in
                self.simple_list_entries(remote_folder_path=remote_folder_path)]

    @response_wrapper
    def simple_upload_via_local(self,
                                local_file_path: str,
                                remote_file_path: str = "/DEFAULT/",
                                excepted_name: str = None) -> dict:
        """
        :param local_file_path:
        :param remote_file_path:
        :param excepted_name:
        :return:
        """
        return SimpleFileMetadata(self.upload(local_file_path=local_file_path,
                                              remote_file_path=remote_file_path,
                                              excepted_name=excepted_name)).to_dict()

    @response_wrapper
    def simple_upload_via_url(self, external_url: str, remote_file_path: str = "/DEFAULT/", **kwargs) -> dict:
        """
        :param external_url:
        :param remote_file_path:
        :return:
        """
        excepted_name = kwargs.get("excepted_name")
        if not is_blank(excepted_name):
            return sda.upload_from_external(external_url=external_url, remote_folder_path=remote_file_path,
                                            excepted_name=excepted_name).to_dict()
        return sda.upload_from_external(external_url=external_url, remote_folder_path=remote_file_path).to_dict()

    @response_wrapper
    def simple_download(self,
                        local_file_path: str,
                        remote_file_path: str,
                        excepted_name: str = None) -> dict:
        """

        :param local_file_path:
        :param remote_file_path:
        :param excepted_name:
        :return:
        """
        return SimpleFileMetadata(self.download(local_file_path=local_file_path,
                                                remote_file_path=remote_file_path,
                                                excepted_name=excepted_name)).to_dict()


# restful API

import flask

app = flask.Flask(__name__, template_folder="../templates")
sda = SimpleDBXServiceAPI(access_token=ACCESS_TOKEN)

from queue import Queue
from concurrent.futures import ThreadPoolExecutor

thread_pool = ThreadPoolExecutor(10)
queue_pool = Queue(10)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", )


@app.route("/api/dropbox/folder/list", methods=['GET', 'POST'])
def list_folder():
    """
    sample as :
    /api/dropbox/folder/list?rfn=default
    :return:
    """
    rfn = request.args.get("remote_folder_name") or request.args.get("rfn")
    if is_blank(rfn):
        return flask.jsonify(
            {"response": "remote folder name is blank in '/api/dropbox/folder/list'", "success": False})
    if not rfn.startswith("/"):
        rfn = "/" + rfn
    if not rfn.endswith("/"):
        rfn = rfn + "/"
    res = sda.simple_list(remote_folder_path=rfn)
    return flask.jsonify(res)


@app.route("/api/dropbox/file/upload", methods=['GET', 'POST'])
def upload_file_from_external_url():
    """
    sample as:
    /api/dropbox/file/upload?eu=https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png
    :return:
    """
    eu = request.args.get("external_url") or request.args.get("eu")
    if is_blank(eu):
        return flask.jsonify({"response": "external url is blank in '/api/dropbox/file/upload'", "success": False})
    en = request.args.get("excepted_name") or request.args.get('en')

    # if not queue_pool.full():
    #     pass
    future = thread_pool.submit(fn=sda.simple_upload_via_url, external_url=eu, excepted_name=en)
    if future.done():
        return flask.jsonify(future.result())
    res = sda.simple_upload_via_url(external_url=eu, excepted_name=en)
    return flask.jsonify(res)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']


@app.route('/view/dropbox/file/upload', methods=['GET', 'POST'])
def upload_file():
    """
    sample as :
    /view/dropbox/file/upload
    :return:
    """
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            sda.upload_from_bytes(file.read(), "/DEFAULT/", filename)
    return '''
    <!doctype html>
    <title>上传文件</title>
    <h1>上传文件</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=确认上传>
    </form>
    '''


async def write_to_file(file_path: str, w_data: bytes) -> None:
    with open_file(file_name=file_path, mode='wb') as f_w:
        f_w.write(w_data)


def cache_with_coroutine(file_path: str, w_data: bytes) -> None:
    coroutine = write_to_file(file_path, w_data)
    # new_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_loop)
    LOOP.run_until_complete(coroutine)


@app.route('/showtime')
def showtime():
    """
    直接名称：/showtime?rfn=/DEFAULT/googlelogo_color_272x92dp.png
    模糊查询名称：/showtime?rfn=google
    模糊查询名称：/showtime?rfn=/DEFAULT/google
    :return:
    """
    rfn = request.args.get("remote_file_name") or request.args.get("rfn")
    if is_blank(rfn):
        return flask.jsonify({"response": "remote file name is blank in '/showtime'", "success": False})

    rf_path, rf_name = separate_path_and_name(rfn)
    if is_blank(rf_name):
        return flask.jsonify({"response": "rf name is blank in '/showtime'", "success": False})

    # 优先使用本地缓存
    local_cache_path = os.path.join(os.getcwd(), "DEFAULT")
    if not os.path.exists(local_cache_path):
        os.mkdir(local_cache_path)
    else:
        filter_file_list = list(filter(lambda x: str(x).__contains__(rf_name), os.listdir(local_cache_path)))
        if len(filter_file_list) > 0:
            cache_file_name = filter_file_list[0]
            # 缓存中目标文件路径
            target_cache_file_path = os.path.join(local_cache_path, cache_file_name)
            if os.path.exists(target_cache_file_path) and os.path.isfile(target_cache_file_path):
                file_suffix = target_cache_file_path.split(".")[-1]
                file_mime = get_mime(file_suffix)
                with open_file(target_cache_file_path, 'rb') as f_read:
                    return flask.send_file(
                        io.BytesIO(f_read.read()),
                        attachment_filename=cache_file_name,
                        mimetype=file_mime
                    )

    # path 为空，只保留文件名，例如：googlelogo_color_272x92dp.png
    if is_blank(rf_path.replace("/", "")):

        # 默认 default 目录
        rf_path = "/DEFAULT/"
        rsl = sda.simple_list(remote_folder_path=rf_path)
        if not rsl.get("success"):
            return flask.jsonify({"response": rsl.get("response"), "success": False})
        for item in rsl.get("response"):
            real_name = item.get("name")
            if str(real_name).__contains__(rf_name):
                file_suffix = real_name.split(".")[-1]
                file_mime = get_mime(file_suffix)

                md, res = sda.download_to_response(remote_file_path=item.get("path"))

                # cache file via coroutine
                local_cache_file = os.path.join(local_cache_path, real_name)
                cache_with_coroutine(file_path=local_cache_file, w_data=res.content)

                return flask.send_file(
                    io.BytesIO(res.content),
                    attachment_filename=real_name,
                    mimetype=file_mime
                )
        # can not match with remote files
        return flask.jsonify({"response": "rf name can not match with remote files in '/showtime'", "success": False})
    # path 不为空，文件名也不为空，例如：/DEFAULT/googlelogo_color_272x92dp.png
    else:
        file_suffix = rfn.split(".")[-1] or rf_name.split(".")[-1]
        file_mime = get_mime(file_suffix)
        try:
            md, res = sda.download_to_response(remote_file_path=rfn)
            # cache file via coroutine
            local_cache_file = os.path.join(local_cache_path, rf_name)
            cache_with_coroutine(file_path=local_cache_file, w_data=res.content)
            return flask.send_file(
                io.BytesIO(res.content),
                attachment_filename=rf_name,
                mimetype=file_mime
            )

        except Exception as ex:
            rsl = sda.simple_list(remote_folder_path=rf_path)
            if not rsl.get("success"):
                return flask.jsonify({"response": rsl.get("response"), "success": False})
            for item in rsl.get("response"):
                real_name = item.get("name")
                if str(real_name).__contains__(rf_name):
                    file_suffix = real_name.split(".")[-1] or real_name.split(".")[-1]
                    file_mime = get_mime(file_suffix)
                    md, res = sda.download_to_response(remote_file_path=item.get("path"))
                    # cache file via coroutine
                    local_cache_file = os.path.join(local_cache_path, real_name)
                    cache_with_coroutine(file_path=local_cache_file, w_data=res.content)
                    return flask.send_file(
                        io.BytesIO(res.content),
                        attachment_filename=rf_name,
                        mimetype=file_mime
                    )
            # can not match with remote files
            return flask.jsonify(
                {"response": "rf name can not match with remote files in '/showtime'", "success": False})


# upload demo
# print(sda.simple_upload_via_local(local_file_path='/Users/helix/Dev/PycharmProjects/pyenv_dev/dropbox_api/hello2.txt',
#                                   remote_file_path="/DEFAULT/",
#                                   excepted_name="dev.txt"))
# download demo
# print(sda.simple_download(local_file_path='', remote_file_path="/DEFAULT/dev.txt", excepted_name='hello2.txt'))
# list demo
# print(sda.list(remote_folder_path="/DEFAULT/"))
# simple list
# print(sda.simple_list(remote_folder_path="/DEFAULT/"))

# upload from external
# sda.upload_from_external(
#     external_url='http://masnun.com/2016/09/18/python-using-the-requests-module-to-download-large-files-efficiently.html',
#     remote_folder_path="/DEFAULT/", custom_headers={"User-Agent": "fake"}, )
#
#


def dropbox_cli():
    """
    cli
    :return:
    """
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
