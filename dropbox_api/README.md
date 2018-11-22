## Simple Dropbox API

----

### start in 5 minutes

1. upload from local file

```python

from dropbox_api.dropbox_api import *

sda = SimpleDropboxAPIV2(access_token="DROPBOX_ACCESS_TOKEN")

def local_upload():
    # simple upload from local file
    aa = sda.upload_from_local(
            local_file_path=r"C:\Helixcs\v2-6130c5c395606f046a845fb7f1d4094f_hd.jpg",
            remote_folder_path="DEFAULT1", )
    print(aa)
    # {'id': 'id:Oq3pERETxccAAAAAAAAFEg', 'name': 'v2-6130c5c395606f046a845fb7f1d4094f_hd.jpg', 'path': '/DEFAULT1/v2-6130c5c395606f046a845fb7f1d4094f_hd.jpg', 'time': datetime.datetime(2018, 11, 11, 17, 47, 38), 'type': 'file', 'hash': 'c94c5781379135c0a8b8eeb1e6b3e25156f5da39f0435b17dcf3f86d77d38d95'}

    aa = sda.upload_from_local(
            local_file_path=r"C:\Helixcs\v2-6130c5c395606f046a845fb7f1d4094f_hd.jpg",
            remote_file_path="/DEFAULT/",
            excepted_name=None)
    print(aa)

    # {'id': 'id:Oq3pXXXXXXXXXXAw', 'name': 'v2-6130c5c395606f046a845fb7f1d4094f_hd.jpg', 'path': '/DEFAULT/v2-6130c5c395606f046a845fb7f1d4094f_hd.jpg', 'time': datetime.datetime(2018, 11, 11, 15, 5, 41), 'type': 'file', 'hash': 'c94c5781379XXXXXXXXXXXXXXXXX77d38d95'}


    # friendly custom source name without suffix , and auto check suffix from local file
    aa = sda.upload_from_local(
        local_file_path=r"C:\Helixcs\v2-6130c5c395606f046a845fb7f1d4094f_hd.jpg",
        remote_file_path="/DEFAULT/vvvv",
        excepted_name=None)
    print(aa)

    # {'id': 'id:Oq3pXXXXXXXXXXAw', 'name': 'vvvv.jpg', 'path': '/DEFAULT/vvvv.jpg', 'time': datetime.datetime(2018, 11, 10, 19, 54, 43), 'type': 'file', 'hash': 'c94c5781379XXXXXXXXXXXXXXXXX77d38d95'}


    # upload with excepted name

    # first priority is     `excepted_name`
    # second priority is    `remote_file_path`
    # third priority is     `local_file_path`

    aa = sda.upload_from_local(
        local_file_path=r"C:\Helixcs\v2-6130c5c395606f046a845fb7f1d4094f_hd",
        remote_file_path="/DEFAULT/mm",
        excepted_name="/DEFAULT1/cat")
    print(aa)

    # {'id': 'id:Oq3pERETxccAAAAAAAAFEQ', 'name': 'cat', 'path': '/DEFAULT1/cat', 'time': datetime.datetime(2018, 11, 11, 17, 34, 12), 'type': 'file', 'hash': 'c94c5781379135c0a8b8eeb1e6b3e25156f5da39f0435b17dcf3f86d77d38d95'}

    aa = sda.upload_from_local(
        local_file_path=r"C:\Helixcs\v2-6130c5c395606f046a845fb7f1d4094f_hd",
        remote_file_path="/DEFAULT/mm",
        remote_folder_path="DEFAULT1",
        excepted_name="/DEFAULT1/cat")
    print(aa)

    # {'id': 'id:Oq3pERETxccAAAAAAAAFEQ', 'name': 'cat', 'path': '/DEFAULT1/cat', 'time': datetime.datetime(2018, 11, 11, 17, 34, 12), 'type': 'file', 'hash': 'c94c5781379135c0a8b8eeb1e6b3e25156f5da39f0435b17dcf3f86d77d38d95'}


```


2. upload source from external url

```python
from dropbox_api.dropbox_api import *

sda = SimpleDropboxAPIV2(access_token="DROPBOX_ACCESS_TOKEN")

def test_url_upload():
    aa = sda.upload_from_external_url(
        external_url="https://desolate-ravine-49980.herokuapp.com/static/de",
        remote_file_path="/DEFAULT/mm",
        excepted_name=None)
    print(aa)

    # {'id': 'id:Oq3pERETxccAAAAAAAAFFA', 'name': 'mm.png', 'path': '/DEFAULT/mm.png', 'time': datetime.datetime(2018, 11, 11, 18, 16, 4), 'type': 'file', 'hash': '74496cc9b6fd263691b78fa4f1e9bfbe404f1a07f0914cfeed7d0cae349352e9'}

    aa = sda.upload_from_external_url(
        external_url="https://desolate-ravine-49980.herokuapp.com/static/de",
        remote_file_path="/DEFAULT/mm",
        excepted_name="lmdkda.png")
    print(aa)

    #
    # aa = sda.upload_from_external_url(
    #     external_url="https://docs.spring.io/spring/docs/current/spring-framework-reference/pdf/data-access.pdf",
    #     remote_file_path=None,
    #     remote_folder_path="DEFAULT1",
    #     excepted_name=None, headers={"user-agent": "testOk"})
    # print(aa)
    #
    # aa = sda.upload_from_external_url(
    #     external_url="https://docs.spring.io/spring/docs/current/spring-framework-reference/pdf/integration.pdf",
    #     remote_file_path=None,
    #     remote_folder_path="DEFAULT1",
    #     excepted_name=None, headers={"user-agent": "testOk"})
    # print(aa)


# test_url_upload()

def test_upload():
    aa = sda.upload(upload_flag="url", external_url="https://desolate-ravine-49980.herokuapp.com/static/de",
                    remote_file_path="/DEFAULT/mm",
                    excepted_name="lmdkda.png")
    print(aa)


```

2. download

```python

from dropbox_api.dropbox_api import *

sda = SimpleDBXServiceAPI(access_token="DROPBOX_ACCESS_TOKEN")
print(sda.download(local_file_path='', remote_file_path="/DEFAULT/Hello.txt", excepted_name='hello.txt'))

```

3. list

```python

from dropbox_api import SimpleDBXServiceAPI

sda = SimpleDBXServiceAPI(access_token="DROPBOX_ACCESS_TOKEN")
print(sda.list(remote_folder_path="/DEFAULT/"))

```

4. 