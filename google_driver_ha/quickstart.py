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

import socks

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


# socks.set_default_proxy(proxy_type=socks.SOCKS5, addr="127.0.0.1", port=1081, rdns="1.1.1.1")
# socket.socket = socks.socksocket
if __name__ == '__main__':
    # main()
    from google_driver_ha.gigu import Gigu

    gigu = Gigu(credential_file_path="credentials.json")

    # https://developers.google.com/drive/api/v3/search-parameters
    items = gigu.list_invoke(q="name contains '纲'", pageSize=200,
                             fields="nextPageToken, files(id, name,mimeType,md5Checksum,size)")
    print(items)
    # print(gigu.simple_create_folder(folder_name="纲"))
    print(gigu.simple_upload(file_path=r"C:\Users\wb-zj268791\Desktop\1_3_banner_dark.png",
                             excepted_name="1_3_banner_dark.png"))
