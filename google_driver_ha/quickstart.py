# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://iliangqunru.bitcron.com/
 File: quickstart.py
 Time: 2018/12/3
 
 Add New Functional quickstart.py
"""
import logging
import socket
import sys

import requests
import socks
from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
PY3 = False

if sys.version > '3':
    PY3 = True

from googleapiclient.discovery import build

from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'


def main():
    store = file.Storage(filename="token.json")
    creds = store.get()

    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets("credentials.json", SCOPES)
        creds = tools.run_flow(flow=flow, storage=store)

    service = build('drive', 'v3', http=creds.authorize(Http()))
    # https://developers.google.com/drive/api/v3/reference/files
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name,mimeType,md5Checksum,size)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'name={0} (id={1} , mime={2})'.format(item['name'], item['id'], item['mimeType']))


socks.set_default_proxy(proxy_type=socks.SOCKS5, addr="127.0.0.1", port=1081, rdns="1.1.1.1")
socket.socket = socks.socksocket
if __name__ == '__main__':
    # main()
    from google_driver_ha.gigu import Gigu, transform_mime

    gigu = Gigu(credential_file_path="credentials.json")
    drive_service = gigu.get_service()

    # https://developers.google.com/drive/api/v3/search-parameters
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and name contains 'XXX'",
        pageSize=200,
        pageToken=None,
        fields="nextPageToken, files(id, name,mimeType,md5Checksum,size)").execute()

    items = results.get("files", [])
    print("==> get remote google drive folder is %s" % items)

    folder_id = None

    if items is None or len(items) < 1:
        # create remote google drive folder
        # ge-uploads

        folder_created_metadata = {'name': 'XXX',
                                   'mimeType': 'application/vnd.google-apps.folder',
                                   'description': "Alibaba 上传分类",
                                   'folderColorRgb': '#FF0000'}

        folder_created = drive_service.files() \
            .create(body=folder_created_metadata,
                    fields="id, name, mimeType,description,md5Checksum,size").execute()
        print("==> created new folder  metadata is %s" % folder_created)
        folder_id = folder_created.get("id")
    else:
        folder_id = items[0].get("id")

    print("folder_id is = %s" % folder_id)

    #  upload file from local path
    file_upload_metadata = {"name": "TCPIP%20Illustrated,%20Volume%201,%202nd%20Edition.pdf", "description": "",
                            "parents": [folder_id]}
    # media_upload = MediaFileUpload(filename=r"C:\Users\wb-zj268791\Desktop\1_3_banner_dark.png",
    #                                     mimetype=transform_mime("png"),
    #                                     resumable=True)

    res = requests.get(url="http://file.allitebooks.com/20150523/TCPIP%20Illustrated,%20Volume%201,%202nd%20Edition.pdf")
    media_upload = MediaInMemoryUpload(body=res.content,
                                       # mimetype=transform_mime("png"),
                                       chunksize=100 * 1024 * 1024,
                                       resumable=True)

    file_upload = drive_service.files() \
        .create(body=file_upload_metadata,
                media_body=media_upload,
                fields="id, name, mimeType,description,md5Checksum,size", ).execute()

    print("==> file upload is %s" % file_upload)
