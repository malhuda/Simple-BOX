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
import socket
import sys
import threading
from typing import List, Optional, Tuple, Any, IO

import dropbox
import requests
import socks
from dropbox.files import FileMetadata, ListFolderResult
from flask import flash, request, redirect, render_template
from requests import Response
from werkzeug.utils import secure_filename

from py_fortify import is_not_blank, is_blank, open_file, FilePathParser, UrlPathParser, get_suffix, assert_state

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logger.setLevel(level)

ACCESS_TOKEN = 'i8G-xobvWUQAAAAAAAABAAzg8_EbfSdZJIGzH93kXBoBGloa7jJuHEUJ167U34eC'

DROPBOX_FILE_SEP = "/"
DROPBOX_FILE_DOT = "."

_FILEMETADATA_LIST_TYPE = List[FileMetadata]
_FILEMETADATA_TYPE = FileMetadata
_BOOLEAN_TYPE = bool
_DICT_TYPE = dict
_STR_TYPE = str
_OPTION_STR = Optional[_STR_TYPE]

try:
    assert sys.version_info.major == 3
    assert sys.version_info.minor > 5
except Exception as ex:
    raise AssertionError("dropbox-api only support 3.6+.")


def is_debug():
    return logger.level == logging.DEBUG


# TODO dropbox content hash compute , https://github.com/dropbox/dropbox-api-content-hasher/blob/master/python/dropbox_content_hasher.py

#  ==>>> single common methods

class DropboxAPIException(Exception):
    def __init__(self, message) -> None:
        self.message = message


class SimpleAPIException(Exception):
    def __init__(self, message) -> None:
        self.message = message


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
        return self.dropbox_file_metadata.content_hash if hasattr(self.dropbox_file_metadata, 'content_hash') \
            else id(self.name)

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

    def upload(self, *args, **kwargs):
        pass

    def download(self, *args, **kwargs):
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

        return self.dbxa.files_upload(file_bytes, remote_file_path, mode=dropbox.files.WriteMode.overwrite, mute=True)

    is_first_chunk = False

    def upload_large_file_with_io(self, remote_file_path: str, upload_bytes: bytes, tell_size:int, file_size: int):
        if self.dbxa is None:
            self.dbx()

        def _first_blood():
            upload_session_start_result = self.dbxa.files_upload_session_start(upload_bytes)
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=tell_size)
            is_first_chunk = True

            pass



        def _finish_blood():
            is_first_chunk = False


        pass

    def upload_large_file(self, local_file_path: str, remote_file_path: str, chunk_size: int) -> _FILEMETADATA_TYPE:
        """
        upload large file
        :param local_file_path:         local file path
        :param remote_file_path:        remote file path
        :param chunk_size:              chunk size
        :return:                        dropbox metadata
        """

        chunk_size = chunk_size or 10 * 1024 * 1024
        file_size = os.path.getsize(local_file_path)
        if self.dbxa is None:
            self.dbx()
        with open_file(file_name=local_file_path, mode="rb") as file_read:
            upload_session_start_result = self.dbxa.files_upload_session_start(file_read.read(chunk_size))
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                       offset=file_read.tell())
            commit = dropbox.files.CommitInfo(path=remote_file_path)

            while file_read.tell() < file_size:
                if is_debug():
                    logger.debug("#upload_large_file , file read frame :{} ".format(file_read.tell()))

                if (file_size - file_read.tell()) < chunk_size:
                    return self.dbxa.files_upload_session_finish(
                        file_read.read(chunk_size),
                        cursor,
                        commit)
                else:
                    self.dbxa.files_upload_session_append(file_read.read(chunk_size),
                                                          cursor.session_id,
                                                          cursor.offset)
                    cursor.offset = file_read.tell()

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

    def async_upload_with_large_file(self, local_file_path: str,
                                     remote_file_path: str,
                                     chunk_size: int) -> _FILEMETADATA_TYPE:
        """
        async upload with large file
        :param local_file_path:
        :param remote_file_path:
        :param chunk_size:
        :return:
        """

        async def _upload_with_large_file():
            async def _inner_upload():
                return self.upload_large_file(local_file_path=local_file_path,
                                              remote_file_path=remote_file_path,
                                              chunk_size=chunk_size)

            return await _inner_upload()

        return self.loop.run_until_complete(_upload_with_large_file())

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
            # `/EXCEPTED_DIR/dog.jpg`

            >>> self.download_as_file(local_file_path='/foo/bar.jpg',remote_folder_path='REMOTE_FOLDER',
            >>> excepted_name='dog.jpg')
            # `/REMOTE_FOLDER/dog.jpg`


        :return:
        """

        global metadata
        if is_blank(remote_file_path):
            if is_blank(remote_folder_path):
                raise DropboxAPIException(
                    "#upload_from_local, remote_file_path is blank and remote_folder_path "
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
            raise DropboxAPIException("#upload_from_local, local file path is blank !")

        if lfpp.is_not_exist:
            raise DropboxAPIException("#upload_from_local, local file path is not exist !")

        if lfpp.is_not_file:
            raise DropboxAPIException("#upload_from_local, local file path is not a file !")

        rfpp = FilePathParser(full_path_file_string=remote_file_path)
        if is_not_blank(excepted_name):
            if DROPBOX_FILE_SEP in excepted_name:
                remote_file_path = DROPBOX_FILE_SEP + excepted_name if not excepted_name.startswith(
                    DROPBOX_FILE_SEP) else excepted_name
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

        file_size = os.path.getsize(local_file_path)
        chunk_size = 10 * 1024 * 1024
        if file_size <= chunk_size:
            if is_debug():
                logger.debug("> uploading tiny file")
            with open_file(file_name=local_file_path, mode="rb") as fr:
                metadata = self.async_upload_bytes(file_bytes=fr.read(), remote_file_path=remote_file_path)
        else:
            if is_debug():
                logger.debug("> uploading large file")
                metadata = self.async_upload_with_large_file(local_file_path=local_file_path,
                                                             remote_file_path=remote_file_path, chunk_size=chunk_size)

        if logger.level == logging.DEBUG:
            logger.debug("upload_from_local metadata is %s" % metadata)
        return metadata

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

    def upload(self,
               upload_flag: str = "local",
               *args,
               **kwargs) -> SimpleFileMetadata:
        """
        upload to remote file
        :param upload_flag  default   `local` , if `local` upload from local ; if `url` upload from external url;
        :return:
        """

        if is_debug():
            logger.debug("SimpleDropboxAPI#upload args=%s , kwargs=%s" % (args, kwargs))

        if upload_flag == 'local':
            return self.upload_from_local(*args, **kwargs)
        elif upload_flag == 'url':
            return self.upload_from_external_url(*args, **kwargs)

        else:
            raise DropboxAPIException(message="#upload , unknown upload flag !")

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
                                    remote_file_path: str) -> Tuple[SimpleFileMetadata, Response]:
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

    def download_as_response(self, remote_file_path: str) -> Response:
        """
        download as response
        remote file path is not blank
        :param remote_file_path:        remote file path in dropbox
        :return:                        requests.Response
        """
        assert is_not_blank(remote_file_path)
        _, response = self.async_download_from_dropbox(remote_file_path=remote_file_path)
        return response

    def download_as_bytes(self, remote_file_path: str) -> bytes:
        """
        download as bytes
        remote file path is not blank
        :param remote_file_path:        remote file path in dropbox
        :return:                        byte array
        """
        assert is_not_blank(remote_file_path)
        return self.download_as_response(remote_file_path=remote_file_path).content

    def download_as_file(self,
                         remote_file_path: str,
                         local_file_path: str,
                         excepted_name: str, ) -> SimpleFileMetadata:
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

        # fix if local folder is not exist , or create it
        if not os.path.exists(lfpp.source_path):
            os.mkdir(lfpp.source_path)

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
        with open_file(file_name=local_file_path, mode="wb") as lwf:
            lwf.write(buffer.getvalue())

        if not buffer.closed():
            buffer.close()
        return simple_file_metadata

    def download(self,
                 *args,
                 **kwargs) -> SimpleFileMetadata:
        """
        download file from dropbox
        :return:
        """
        return self.download_as_file(*args, **kwargs)
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

        if is_blank(remote_folder_path):
            raise DropboxAPIException("#list ,  remote folder path is blank !")

        remote_folder_path = DROPBOX_FILE_SEP + remote_folder_path if not remote_folder_path.startswith(
            DROPBOX_FILE_SEP) else remote_folder_path

        remote_folder_path = remote_folder_path + DROPBOX_FILE_SEP if not remote_folder_path.endswith(
            DROPBOX_FILE_SEP) else remote_folder_path

        return self.async_list(remote_folder_path=remote_folder_path)


class SimpleWrapper(object):
    def __init__(self, *args, **kwargs):
        pass

    def upload_folder(self, *args, **kwargs):
        pass

    def download_folder(self):
        pass

    def sync_folder(self):
        pass

    # ...


from concurrent.futures import ThreadPoolExecutor

upload_file_pool = ThreadPoolExecutor(100)


class DropboxWrapper(SimpleWrapper, SimpleDropboxAPIV2):
    def __init__(self, *args, **kwargs):
        SimpleWrapper.__init__(self, *args, **kwargs)
        SimpleDropboxAPIV2.__init__(self, *args, **kwargs)

    def upload_folder(self,
                      local_file_folder: str,
                      remote_file_folder: str = None):

        lfpp = FilePathParser(full_path_file_string=local_file_folder)
        if is_blank(lfpp.source_path):
            raise DropboxAPIException(message="#upload_folder , local file folder is blank !")
        if not os.path.exists(lfpp.source_path):
            raise DropboxAPIException(message="#upload_folder , local file folder is not exist !")
        if not os.path.isdir(lfpp.source_path):
            raise DropboxAPIException(message="#upload_folder , local file folder is not folder !")

        if is_not_blank(remote_file_folder):
            remote_file_folder = DROPBOX_FILE_SEP + remote_file_folder if not remote_file_folder.startswith(
                DROPBOX_FILE_SEP) else remote_file_folder
            remote_file_folder = remote_file_folder + DROPBOX_FILE_SEP if not remote_file_folder.endswith(
                DROPBOX_FILE_SEP) else remote_file_folder

        def gen_local_file_path(folder: str):
            global roots, dirs
            for roots, dirs, files in os.walk(top=folder):
                for _file in files:
                    local_file_path = os.path.join(roots, _file)
                    _f = FilePathParser(full_path_file_string=local_file_path)
                    remote_file_path = _f.translate_to_linux_file()
                    yield local_file_path, remote_file_path, _f.source_name

            if len(dirs) > 0:
                for _dir in dirs:
                    local_folder_path = os.path.join(roots, _dir)
                    gen_local_file_path(folder=local_folder_path)

        for glfp in gen_local_file_path(folder=local_file_folder):
            _local_file_path = glfp[0]
            _remote_file_path = glfp[1]
            _source_file_name = glfp[2]
            if is_not_blank(remote_file_folder):
                _remote_file_path = os.path.join(remote_file_folder, _source_file_name)

            if is_debug():
                logger.debug("%s ==> %s " % (_local_file_path, _remote_file_path))
            # md = self.upload(local_file_path=_local_file_path, remote_file_path=_remote_file_path)
            # print(md)
            future = upload_file_pool.submit(fn=self.upload,
                                             local_file_path=_local_file_path,
                                             remote_file_path=_remote_file_path)

        pass

    def download_folder(self):
        pass

    def sync_folder(self):
        pass


# ================================>

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


class SimpleDBXServiceAPI(SimpleDropboxAPIV2):

    # service implement
    def __init__(self, access_token) -> None:
        super().__init__(access_token=access_token)

    @response_wrapper
    def simple_list(self, remote_folder_path: str) -> List[dict]:
        """
        simple metadata list
        :param remote_folder_path:
        :return:
        """

        assert_state(is_blank(pstr=remote_folder_path),
                     "SimpleDBXServiceAPI#simple_list , remote_folder_path is blank !")
        return [SimpleFileMetadata(sfm).to_dict() for sfm in self.list(remote_folder_path=remote_folder_path).entries]

    @response_wrapper
    def simple_upload_from_local(self,
                                 local_file_path: str,
                                 remote_file_path: str = None,
                                 excepted_name: str = None) -> dict:
        """
        :param local_file_path:
        :param remote_file_path:
        :param excepted_name:
        :return:
        """
        lfpp = FilePathParser(full_path_file_string=local_file_path)
        assert_state(lfpp.is_blank, "SimpleDBXServiceAPI#simple_upload_from_local , local_file_path is blank !")
        assert_state(lfpp.is_not_exist, "SimpleDBXServiceAPI#simple_upload_from_local ,local_file_path is not exist !")

        remote_file_path = remote_file_path or "DEFAULT"

        return self.upload(local_file_path=local_file_path,
                           remote_file_path=remote_file_path,
                           excepted_name=excepted_name).to_dict()

    @response_wrapper
    def simple_upload_from_url(self,
                               external_url: str,
                               remote_file_path: str = None,
                               excepted_name: str = None,
                               **kwargs) -> dict:
        """
        :param excepted_name:
        :param external_url:
        :param remote_file_path:
        :return:
        """
        expp = UrlPathParser(full_path_file_string=external_url)
        assert_state(expp.is_blank, "SimpleDBXServiceAPI#simple_upload_from_url , external_url is blank !")
        assert_state(expp.is_not_http,
                     "SimpleDBXServiceAPI#simple_upload_from_url , external_url is not http protocol !")

        return sda.upload(upload_flag="url",
                          external_url=external_url,
                          remote_file_path=remote_file_path,
                          excepted_name=excepted_name,
                          **kwargs).to_dict()


# restful API Samples

import flask

LOOP = asyncio.get_event_loop()

app = flask.Flask(__name__, template_folder="../templates")
sda = SimpleDBXServiceAPI(access_token=ACCESS_TOKEN)

from queue import Queue
from concurrent.futures import ThreadPoolExecutor

thread_pool = ThreadPoolExecutor(10)
queue_pool = Queue(10)

dropbox_rest_main_url = "/api/dropbox/"
dropbox_view_main_url = "/view/dropbox/"


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", )


@app.route(dropbox_rest_main_url + "folder/list", methods=['GET', 'POST'])
def list_folder():
    """
    sample as :
    /api/dropbox/folder/list?rfp=default
    :return:
    """
    rfp = request.args.get("remote_folder_path") or request.args.get("rfp")
    res = sda.simple_list(remote_folder_path=rfp)
    return flask.jsonify(res)


@app.route(dropbox_rest_main_url + "file/upload", methods=['GET', 'POST'])
def upload_from_external_url():
    """
    sample as:
    /api/dropbox/file/upload?eu=https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png
    :return:
    """
    eu = request.args.get("external_url") or request.args.get("eu")
    en = request.args.get("excepted_name") or request.args.get('en')
    rfp = request.args.get("remote_file_path") or request.args.get('rfp') or "/DEFAULT/"

    res = sda.simple_upload_from_url(external_url=eu, remote_file_path=rfp, excepted_name=en)
    return flask.jsonify(res)


@app.route(dropbox_view_main_url + 'file/upload', methods=['GET', 'POST'])
def upload_file_from_local():
    """
    /view/dropbox/file/upload
    :return:
    """

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif']

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
            remote_file_path = os.path.join("/DEFAULT/", filename)
            sda.async_upload_bytes(file_bytes=file.read(), remote_file_path=remote_file_path)
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


@app.route(dropbox_view_main_url + 'showtime')
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
                tfpp = FilePathParser(full_path_file_string=target_cache_file_path)
                file_mime = get_mime(tfpp.source_suffix)
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

                content = sda.download_as_bytes(remote_file_path=item.get("path"))

                # cache file via coroutine
                local_cache_file = os.path.join(local_cache_path, real_name)
                cache_with_coroutine(file_path=local_cache_file, w_data=content)

                return flask.send_file(
                    io.BytesIO(content),
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
            md, res = sda.download_as_bytes(remote_file_path=rfn)
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
                    md, res = sda.download_as_bytes(remote_file_path=item.get("path"))
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


def dropbox_cli():
    """
    cli
    :return:
    """
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
