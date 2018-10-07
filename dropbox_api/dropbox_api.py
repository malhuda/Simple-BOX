# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: dropbox_api.py
 Time: 10/4/18
"""
from __future__ import print_function

import logging
import os
import dropbox
import re
import requests
import io
from contextlib import contextmanager
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from dropbox.files import FileMetadata, ListFolderResult
from typing import List, AnyStr

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logger.setLevel(level)

ACCESS_TOKEN = 'i8G-xobvWUQAAAAAAAABAAzg8_EbfSdZJIGzH93kXBoBGloa7jJuHEUJ167U34eC'

FILE_SEP = "/"
FILE_DOT = "."

FILEMETADATA_LIST_TYPE = List[FileMetadata]
FILEMETADATA_TYPE = FileMetadata
BOOLEAN_TYPE = bool
DICT_TYPE = dict
STR_TYPE = str


class DropboxAPIException(Exception):
    def __init__(self, message) -> None:
        self.message = message


@contextmanager
def open_file(file_name: str, mode: str = 'wb'):
    file = open(file=file_name, mode=mode)
    yield file
    file.flush()
    file.close()


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


def separate_path_and_name(file_path: str):
    if file_path is None or file_path.strip("") == '':
        return None, None
    fps = file_path.split(FILE_SEP)
    f_name = fps[-1]
    f_path = '/'
    for it in fps[0:-1]:
        f_path = os.path.join(f_path, it)
    f_path = f_path + "/"
    return f_path, f_name


def fetch_filename_from_url(url: str) -> str:
    if url is None or url.strip("") == '':
        return ""
    last_sep = url.split("/")[-1]
    if last_sep.__contains__("?"):
        return re.findall(r'^(.+?)\?', last_sep)[0]
    elif last_sep.__contains__(":"):
        return re.findall(r'^(.+?):', last_sep)[0]
    return last_sep


def get_mime(file_suffix: str) -> str:
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
        return self.dropbox_file_metadata.server_modified if hasattr(self.dropbox_file_metadata,
                                                                     'server_modified') else ""

    @property
    def type(self):
        return "file" if self.time != '' and self.__hash__() != '' else "folder"

    def __hash__(self):
        return self.dropbox_file_metadata.content_hash if hasattr(self.dropbox_file_metadata, 'content_hash') else ""

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'path': self.path, 'time': self.time, 'type': self.type,
                'hash': self.__hash__()}


class SimpleDropboxAPI(object):

    def __init__(self, access_token):
        self.access_token = access_token
        self.dbxa = None

    def dbx(self) -> None:
        dbx = dropbox.Dropbox(self.access_token)
        if dbx is None:
            raise DropboxAPIException("dbx is None!")
        self.dbxa = dbx

    def upload(self, local_file_path: str, remote_file_path: str = "/DEFAULT/",
               excepted_name: str = None) -> FILEMETADATA_TYPE:
        if not os.path.isfile(local_file_path):
            raise DropboxAPIException("local file not exist!")

        if excepted_name is None or excepted_name.strip('') == '':
            excepted_name = local_file_path.split(FILE_SEP)[-1]

        # not exist file name, sample as `/foo/bar/`, in this case , `remote_file_path` will be set as `/foo/bar`+excepted_name
        # if `remote_file_path` is `/foo/bar` or `/foo/bar.txt` ,then `bar` or `bar.txt` will be excepted_name
        if not remote_file_path.__contains__(FILE_DOT) and remote_file_path.split(FILE_SEP)[-1] == '':
            remote_file_path = os.path.join(remote_file_path, excepted_name)

        if self.dbxa is None:
            self.dbx()
        with open_file(file_name=local_file_path, mode='rb') as lf:
            metadata = self.dbxa.files_upload(lf.read(), remote_file_path, mute=True)
        return metadata

    def download(self, local_file_path: str, remote_file_path: str, excepted_name: str = None) -> FILEMETADATA_TYPE:
        """
        download file
        :param local_file_path:
        :param remote_file_path:
        :param excepted_name:
        :return:
        """
        if remote_file_path is None or remote_file_path.strip() == '':
            raise DropboxAPIException("download remote file path is None")

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

    def upload_from_external(self, external_url: str, remote_folder_path: str, **kwargs) -> SimpleFileMetadata:
        """
        upload file which from external url
        :param external_url:
        :param remote_folder_path:
        :param kwargs:
        :return:
        """
        if remote_folder_path is None or remote_folder_path.strip("") == '':
            raise DropboxAPIException("upload remote file path is None!")
        if external_url is None or external_url.strip("") == '':
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

    def upload_from_bytes(self, file_bytes: bytes, remote_folder_path: str, excepted_name: str) -> SimpleFileMetadata:
        """
        upload from bytes
        :param file_bytes:
        :param remote_folder_path:
        :param excepted_name:
        :return:
        """
        if file_bytes is None:
            raise DropboxAPIException("upload from bytes , bytes is None")
        if remote_folder_path is None or remote_folder_path.strip("") == '':
            raise DropboxAPIException("upload from bytes  remote file path is None!")
        rf_path, rf_name = separate_path_and_name(remote_folder_path)
        if excepted_name is not None and not excepted_name.strip("") == '':
            rf_name = excepted_name

        remote_folder_path = os.path.join(rf_path, rf_name)

        if self.dbxa is None:
            self.dbx()
        md = self.dbxa.files_upload(file_bytes, remote_folder_path, mute=True)
        return SimpleFileMetadata(md)

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

    def simple_list_entries(self, remote_folder_path: str) -> FILEMETADATA_LIST_TYPE:
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
    def simple_upload_via_url(self, external_url: str, remote_file_path: str = "/DEFAULT/") -> dict:
        """
        :param external_url:
        :param remote_file_path:
        :return:
        """
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


def is_blank(pstr: str):
    """
    check string whether blank
    :param pstr:
    :return:
    """
    if pstr is None or pstr.strip('') == '':
        return True
    return False


# restful API

import flask

app = flask.Flask(__name__)
sda = SimpleDBXServiceAPI(access_token=ACCESS_TOKEN)


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
    res = sda.simple_upload_via_url(external_url=eu)
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


@app.route("/", methods=['GET'])
def index(): return """ <h1>Welcome To Helixcs's Space. </h1>"""


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

    if is_blank(rf_path.replace("/", "")):
        # 默认 default 目录
        rf_path = "/DEFAULT/"
        rsl = sda.simple_list(remote_folder_path=rf_path)
        if not rsl.get("success"):
            return flask.jsonify({"response": rsl.get("response"), "success": False})
        for item in rsl.get("response"):
            real_name = item.get("name")
            if str(real_name).__contains__(rf_name):
                file_suffix = real_name.split(".")[-1] or real_name.split(".")[-1]
                file_mime = get_mime(file_suffix)

                md, res = sda.download_to_response(remote_file_path=item.get("path"))
                return flask.send_file(
                    io.BytesIO(res.content),
                    attachment_filename=rf_name,
                    mimetype=file_mime
                )
        # can not match with remote files
        return flask.jsonify({"response": "rf name can not match with remote files in '/showtime'", "success": False})
    else:
        file_suffix = rfn.split(".")[-1] or rf_name.split(".")[-1]
        file_mime = get_mime(file_suffix)
        try:
            md, res = sda.download_to_response(remote_file_path=rfn)
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


def drobox_cli():
    """
    cli
    :return:
    """
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

