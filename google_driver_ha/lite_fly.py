# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Since : 3.6
 Author: zhangjian
 Site: https://iliangqunru.bitcron.com/
 File: lite_fly
 Time: 2018/12/20
 
 Add New Functional lite_fly
"""
import logging
import socket
import sys
import queue
import asyncio

import os
import threading
import requests
import socks
import sched, time
from googleapiclient.http import MediaInMemoryUpload, MediaFileUpload
from google_driver_ha import transform_mime
from py_fortify import FilePathParser

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

PY3 = False

SYNC_QUEUE = queue.Queue()
LOOP = asyncio.get_event_loop()

if sys.version > '3':
    PY3 = True

socks.set_default_proxy(proxy_type=socks.SOCKS5, addr="127.0.0.1", port=1081, rdns="1.1.1.1")
socket.socket = socks.socksocket

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'

store = file.Storage("token.json")
creds = store.get()

if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets("credentials.json", SCOPES)
    creds = tools.run_flow(flow=flow, storage=store)
drive_service = build('drive', 'v3', http=creds.authorize(Http()))


async def get_folder(folder_name: str) -> list:
    # https://developers.google.com/drive/api/v3/search-parameters
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and name contains '" + folder_name + "'",
        pageSize=200,
        pageToken=None,
        fields="nextPageToken, files(id, name,mimeType,md5Checksum,size)").execute()

    items = results.get("files", [])
    print("==> get remote google drive folder is %s" % items)
    return items


async def create_folder(folder_name: str) -> dict:
    folder_created_metadata = {'name': folder_name,
                               'mimeType': 'application/vnd.google-apps.folder',
                               'description': folder_name,
                               'folderColorRgb': '#FF0000'}

    folder_created = drive_service.files() \
        .create(body=folder_created_metadata,
                fields="id, name, mimeType,description,md5Checksum,size").execute()
    print("==> created new folder  metadata is %s" % folder_created)
    return folder_created


async def exist_or_create(folder_name: str) -> dict:
    items = await get_folder(folder_name)
    if items is None or len(items) < 1:
        # create remote google drive folder
        return await create_folder(folder_name)
    else:
        return items[0]


from samples import tweets_persistence

_lock = threading.Lock()


def async_fetch_wb(name: str, export_file_path: str) -> None:
    if not os.path.exists(export_file_path):
        os.makedirs(export_file_path)

    async def _inner_fetch():
        tweets_persistence.dispatch(name=name,
                                    pages=None,
                                    is_simplify=True,
                                    persistence_format="txt",
                                    export_file_path=export_file_path,
                                    export_file_name=None,
                                    is_debug=False)

    LOOP.run_until_complete(_inner_fetch())
    # for f in FilePathParser.files_generator(file_path=export_file_path):
    #     with _lock:
    #         SYNC_QUEUE.put(f)
    #


async def upload_to_drive_from_local(local_file_path: str, folder_id: str) -> dict:
    lfpp = FilePathParser(full_path_file_string=local_file_path)
    #  upload file from local path
    file_upload_metadata = {"name": lfpp.source_name,
                            "description": "",
                            "parents": [folder_id]}

    media_upload = MediaFileUpload(filename=lfpp.full_path_file_string,
                                   mimetype=transform_mime(lfpp.source_suffix),
                                   resumable=True)

    file_upload = drive_service.files() \
        .create(body=file_upload_metadata,
                media_body=media_upload,
                fields="id, name, mimeType,description,md5Checksum,size", ).execute()

    # res = requests.get( url="http://file.allitebooks.com/20150523/TCPIP%20Illustrated,%20Volume%201,%202nd%20Edition.pdf")
    # media_upload = MediaInMemoryUpload(body=res.content,
    #                                    # mimetype=transform_mime("png"),
    #                                    chunksize=100 * 1024 * 1024,
    #                                    resumable=True)

    # file_upload = drive_service.files() \
    #     .create(body=file_upload_metadata,
    #             media_body=media_upload,
    #             fields="id, name, mimeType,description,md5Checksum,size", ).execute()
    #

    print("==> file upload is %s" % file_upload)
    return file_upload


async def running_and_upload(local_file_path: str):
    with _lock:
        local_file_path = SYNC_QUEUE.get()
        await upload_to_drive_from_local(local_file_path=local_file_path, folder_id=folder_id)


s = sched.scheduler(time.time, time.sleep)


def run_sched(action, *args):
    s.enter(delay=5, priority=0, action=action, argument=args)
    s.run()


if __name__ == '__main__':
    wb_name = "嘻红豆"
    remote_folder_name = "xxx"
    local_folder_path = "d:\\xixi"

    folder_metadata_future = LOOP.run_until_complete(exist_or_create(folder_name=remote_folder_name))
    print("folder_metadata is = %s" % folder_metadata_future)

    folder_id = folder_metadata_future.get("id")

    # fetch wb
    while True:
        run_sched(async_fetch_wb, wb_name, local_folder_path)
