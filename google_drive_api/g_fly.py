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
import asyncio
import logging
import os
import queue
import socket
import sys
import socks
import argparse
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from googleapiclient.http import MediaFileUpload

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

PY3 = False

SYNC_QUEUE = queue.Queue()
LOOP = asyncio.get_event_loop()
THREAD_POOL = ThreadPoolExecutor(10)
CURRENT_DIR = os.getcwd()

if sys.version > '3':
    PY3 = True

from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive'

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


_lock = threading.Lock()


async def upload_to_drive_from_local(local_file_path: str, folder_id: str) -> dict:
    name = os.path.basename(local_file_path)
    #  upload file from local path
    file_upload_metadata = {"name": name,
                            "description": "",
                            "parents": [folder_id]}

    media_upload = MediaFileUpload(filename=local_file_path,
                                   # mimetype=transform_mime(lfpp.source_suffix),
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


def cli():
    args = sys.argv
    print("==> " + str(args))
    if len(args) < 2:
        raise Exception("illegal fucking args~")
    local_folder_path = args[1]
    remote_folder_name = args[2] or "new Folder"

    socket_proxy = args[3]

    if local_folder_path is None:
        raise Exception("local file path is not none~")

    sure = input("do you want to sure sync {0} ==> {1}  to google drive?".format(local_folder_path, remote_folder_name))
    if str(sure).upper() != 'Y':
        return

    if socket_proxy:
        socket_host = socket_proxy.split(":")[0]
        socket_port = socket_proxy.split(":")[1]
        if not socket_port:
            raise Exception("proxy port is not exist~")
        socks.set_default_proxy(proxy_type=socks.SOCKS5, addr=socket_host, port=socket_port, rdns="1.1.1.1")
        socket.socket = socks.socksocket

    folder_metadata_future = LOOP.run_until_complete(exist_or_create(folder_name="xxx"))
    print("folder_metadata is = %s" % folder_metadata_future)

    folder_id = folder_metadata_future.get("id")

    def scan_local_file_path(folder: str):
        global roots, dirs
        for roots, dirs, files in os.walk(top=folder):
            for _file in files:
                local_file_path = os.path.join(roots, _file)
                yield local_file_path
        if len(dirs) > 0:
            for _dir in dirs:
                local_folder_path = os.path.join(roots, _dir)
                scan_local_file_path(folder=local_folder_path)

    def async_upload(local_file_path: str, remote_folder_id: str) -> dict:
        return LOOP.run_until_complete(
            upload_to_drive_from_local(local_file_path=local_file_path, folder_id=remote_folder_id))

    for fds in scan_local_file_path(folder=local_folder_path):
        gu_future = THREAD_POOL.submit(async_upload, fds, folder_id, )
        gu_result = gu_future.result()
        print("{0} ==> {1}".format(fds, gu_result))
        if gu_result.get("id"):
            os.remove(fds)


def g_test():
    folder_id = LOOP.run_until_complete(exist_or_create(folder_name="dafa")).get("id")
    LOOP.run_until_complete(upload_to_drive_from_local(local_file_path=r"D:\xixi\测试.txt", folder_id=folder_id))


if __name__ == '__main__':
    # cli()
    # pass
    g_test()
