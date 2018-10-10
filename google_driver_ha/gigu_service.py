# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 Site: https://iliangqunru.bitcron.com/
 File: gigu-service.py
 Time: 10/4/18
"""
import logging
from google_driver_ha.gigu import *

level = logging.DEBUG
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = '%Y-%m-%d %H:%M'
logging.basicConfig(level=level, format=format, datefmt=datefmt)
logger = logging.getLogger(__name__)
logger.setLevel(level)

gigu = Gigu('/root/code/pyenv_dev/resources/credentials.json')


def res_tag(func):
    def wrapper(*args, **kwargs):
        ret_wrapper = {'params': [], 'res': None, 'exception': None}
        if args is not None and args.__len__() > 0:
            ret_wrapper['params'].append(args)
        elif kwargs is not None and kwargs.__len__() > 0:
            ret_wrapper['params'].append(kwargs)
        try:
            ret = func(*args, **kwargs)
            ret_wrapper['res'] = ret
        except Exception as ex:
            ret_wrapper['exception'] = ex
        return ret_wrapper

    return wrapper


@res_tag
def create_share_drive_folder(folder_name):
    return gigu.simple_create_folder(folder_name)


@res_tag
def delete_share_drive_folder(folder_id):
    return gigu.delete(folder_id)


@res_tag
def get_file_detail(file_id):
    return gigu.get(file_id)


@res_tag
def _res_tag(name):
    return name
