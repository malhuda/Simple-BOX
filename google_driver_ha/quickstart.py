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
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))


socks.set_default_proxy(proxy_type=socks.SOCKS5, addr="127.0.0.1", port=1081, rdns="1.1.1.1")
socket.socket = socks.socksocket
if __name__ == '__main__':
    # main()
    from google_driver_ha.gigu import Gigu

    gigu = Gigu(credential_file_path="credentials.json")
    gigu.simple_upload(file_path=r"C:\Users\wb-zj268791\Desktop\alibaba\通用\粘贴图片(2).png",
                       excepted_name="粘贴图片(2).png")
