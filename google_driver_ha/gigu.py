# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: gigu.py
 Time: 10/3/18
"""
from __future__ import print_function

import io
import logging
import os

from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logger.setLevel(level)

GOOGLE_API_CLIENT_SERVICE_TYPE = Resource
JSON_TYPE = dict
LIST_TYPE = list

AUTH_SCOPES = 'https://www.googleapis.com/auth/drive'
DEFAULT_CREDENTIAL_PATH = '/root/code/pyenv_dev/resources/credentials.json'

FILE_SEP = "/"
FILE_DOT = "."


def transform_mime(file_suffix: str) -> str:
    if file_suffix is None:
        raise GiguException("file suffix is None !")
    if file_suffix.startswith("."):
        file_suffix = file_suffix.replace(".", "")
    mime_dict = {
        "jpeg": "image/jpeg",
        "jpg": "image/jpg",
        "png": "image/png",
        "csv": "text/csv",
        "pdf": "application/pdf",
        "html": "text/html",
        # ....
    }
    return mime_dict.get(file_suffix)


class GiguException(Exception):
    def __init__(self, message) -> None:
        self.message = message


class BaseAction(object):
    def execute(self):
        pass


class Gigu(BaseAction):
    def __init__(self, credential_file_path):
        super().__init__()
        self.credential_file_path = credential_file_path
        self.driver_service = None

    def get_service(self, ) -> None:
        """ get driver service
            file structure is #reference :https://developers.google.com/drive/api/v3/reference/files
        """
        store = file.Storage('token.json')
        credential = store.get()
        if not credential or credential.invalid:
            if self.credential_file_path is None or not os.path.exists(self.credential_file_path):
                raise GiguException("credential path is not exist!")

            flow = client.flow_from_clientsecrets(self.credential_file_path, AUTH_SCOPES)
            credential = tools.run_flow(flow, store)
        service = build('drive', 'v3', http=credential.authorize(Http()))
        self.driver_service = service

    def create_folder(self, metadata: JSON_TYPE) -> JSON_TYPE:
        """ create folder
        """
        if self.driver_service is None:
            self.get_service()
            # check again
        if self.driver_service is None:
            raise GiguException("driver service is None!")
        if metadata is None:
            raise GiguException("metadata is None!")

        folder_created = self.driver_service.files().create(body=metadata,
                                                            fields='id').execute()
        folder_created['metadata'] = metadata
        if logger.level == logging.DEBUG:
            logger.debug("folder created  is %s", folder_created)
        return folder_created

    def simple_create_folder(self, folder_name) -> JSON_TYPE:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        return self.create_folder(metadata=folder_metadata)

    def delete(self, file_id: str):
        """ delete file by file id"""
        file_deleted = {}
        if self.driver_service is None:
            self.get_service()
            # check again
        if self.driver_service is None:
            raise GiguException("driver service is None!")
        try:
            file_deleted['file_id'] = file_id
            self.driver_service.files().delete(fileId=file_id).execute()
            file_deleted['success'] = True
        except Exception as ex:
            logger.error("delete file by file id:%s occurred an exception : %s", (file_id, ex))
            file_deleted['success'] = False
            file_deleted['message'] = ex
            raise GiguException(ex)
        if logger.level == logging.DEBUG:
            logger.debug("file deleted is %s", file_deleted)
        return file_deleted

    def get(self, file_id: str) -> JSON_TYPE:
        """get by file id"""
        if self.driver_service is None:
            self.get_service()
            # check again
        if self.driver_service is None:
            raise GiguException("driver service is None!")

        file_get = self.driver_service.files().get_media(fileId=file_id).execute()
        if logger.level == logging.DEBUG:
            logger.debug("file get is %s" % file_get)
        return file_get

    def list(self, params: JSON_TYPE, max_size: int) -> LIST_TYPE:
        """ list file items """
        if self.driver_service is None:
            self.get_service()
            # check again
        if self.driver_service is None:
            raise GiguException("driver service is None!")
        result = []
        tmp_size = 0
        while True:
            if tmp_size > max_size:
                break
            files = self.driver_service.files().list(**params).execute()
            result.extend(files['items'])
            page_token = files.get('nextPageToken')

            if not page_token:
                break

            tmp_size += 1

        if logger.level == logging.DEBUG:
            logger.debug("file list params is :%s , result is :%s" % (params, result))
        return result

    def simple_upload(self, file_path: str, excepted_name: str = None, excepted_suffix: str = None) -> JSON_TYPE:
        """simple upload"""
        if self.driver_service is None:
            self.get_service()
            # check again
        if self.driver_service is None:
            raise GiguException("driver service is None!")

        if not os.path.exists(file_path):
            raise Gigu("simple upload file not exist!")
        if excepted_name is None:
            excepted_name = file_path.split(FILE_SEP)[-1]
        if excepted_suffix is None:
            if not excepted_name.__contains__(FILE_DOT):
                if not file_path.__contains__(FILE_DOT):
                    raise Gigu("Unknown file type suffix")
                excepted_suffix = file_path.split(FILE_DOT)[-1]
            else:
                excepted_suffix = excepted_name.split(FILE_DOT)[-1]

        upload_file_metadata = {'name': excepted_name}
        upload_media = MediaFileUpload(filename=file_path, mimetype=transform_mime(excepted_suffix))
        file_created = self.driver_service.files().create(body=upload_file_metadata,
                                                          media_body=upload_media,
                                                          fields="id").execute()
        # file_created['file_path'] = file_path
        if logger.level == logging.DEBUG:
            logger.debug("file created is %s", file_created)
        return file_created

    def download_file(self, file_id: str, mime_type: str):
        if self.driver_service is None:
            self.get_service()
            # check again
        if self.driver_service is None:
            raise GiguException("driver service is None!")
        request = self.driver_service.files().get_media(fileId=file_id, )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if logger.level == logging.DEBUG:
                logger.debug("file :%s , download %d%%." % (file_id, int(status.progress() * 100)))
        if done:
            with open(r'test_dsa.jpg', 'wb') as _f:
                _f.write(fh.getbuffer())

            if not fh.closed:
                fh.close()


# -------------------- demo ----------------------


def create_folder_demo():
    gigu = Gigu(credential_file_path="/root/code/pyenv_dev/resources/credentials.json")
    gigu.simple_create_folder("tester_folder2")
    pass


def upload_file_demo():
    gigu = Gigu(credential_file_path="/root/code/pyenv_dev/resources/credentials.json")
    gigu.simple_upload(file_path="/root/qiniu/ownz-o88t4z7ss.bkt.clouddn.com/0 (1).jpg", excepted_name="梅花")


def delete_file():
    gigu = Gigu(credential_file_path="/root/code/pyenv_dev/resources/credentials.json")
    gigu.delete(file_id='11t2Vbv-1jNiJ3yO--LvM6qw8dJvcXrYT')


def download_file_demo():
    gigu = Gigu(credential_file_path="/root/code/pyenv_dev/resources/credentials.json")
    gigu.download_file(file_id='1s2ve7F2_8-zDp6l7nmjJJ-9H1WoBRpq0', mime_type='')


def list_file_demo():
    gigu = Gigu(credential_file_path="/Users/helix/Dev/PycharmProjects/pyenv_dev/resources/credentials.json")
    gigu.list(params={'pageToken': None, 'orderBy': 'folder', 'pageSize': 10}, max_size=10)

def get_file_demo():
    gigu = Gigu(credential_file_path="/Users/helix/Dev/PycharmProjects/pyenv_dev/resources/credentials.json")
    gigu.get(file_id='1YsfW7UBliUWLUKk4eKsh6OIMZgjJtBZN')




if __name__ == '__main__':
    get_file_demo()
    pass
