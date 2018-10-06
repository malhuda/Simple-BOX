## Simple Dropbox API

----

### start in 5 minutes

1. upload

```python

from dropbox_api import SimpleDBXServiceAPI

sda = SimpleDBXServiceAPI(access_token="DROPBOX_ACCESS_TOKEN")
print(sda.upload(local_file_path='local_dev.png',remote_file_path="/DEFAULT/" , excepted_name="dev.png"))

```

2. download

```python

from dropbox_api import SimpleDBXServiceAPI

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