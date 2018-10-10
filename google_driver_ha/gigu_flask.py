# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: gigu-flask.py
 Time: 10/4/18
"""
import logging
import sys
import os
import requests

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logger.setLevel(level)

from flask import Flask, Request, jsonify
from google_driver_ha.gigu_service import _res_tag, create_share_drive_folder, delete_share_drive_folder, get_file_detail

app = Flask(__name__)


@app.route("/api/res/<name>", methods=['GET'])
def res(name):
    return jsonify(_res_tag(name))


@app.route("/api/google/drive/folder/create/<folder_name>", methods=['GET'])
def api_google_drive_folder_create(folder_name):
    return jsonify(create_share_drive_folder(folder_name))


@app.route("/api/google/drive/folder/delete/<folder_id>", methods=['GET'])
def api_google_drive_folder_delete(folder_id):
    return jsonify(delete_share_drive_folder(folder_id))


@app.route("/api/google/drive/file/get/<file_id>", methods=['GET'])
def api_google_drive_file_get(file_id):
    return jsonify(get_file_detail(file_id))


app.run(host='0.0.0.0', port=8087, debug=True)
