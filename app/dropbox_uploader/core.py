import contextlib
import json
import os
import time

import dropbox
import requests
from django.conf import settings
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode


def split_str(str):
    arr = str.split('-')
    if arr[-1].endswith('.png') or arr[-1].endswith('.jpg') or arr[-1].endswith('.PNG') or arr[-1].endswith('.JPG'):
        arr[-1] = arr[-1][:-4]
    elif arr[-1].endswith('.jpeg'):
        arr[-1] = arr[-1][:-5]
    return arr


def make_url(url):
    if url.endswith('?dl=0'):
        url = url[:-5]
    return url.replace('www.dropbox', 'dl.dropboxusercontent')


API_KEY_DROPBOX = settings.API_KEY_DROPBOX
URL_UPLOAD = "https://content.dropboxapi.com/2/files/upload"
URL_SHARE_LINK = "https://api.dropboxapi.com/2/sharing/create_shared_link"
HEADERS_TO_UPLOAD = {
    "Authorization": "Bearer M6iN1nYzh_YAAAAAAACHm34PsRKmgPWvVI6uSALYMTqZxGUcopC4pr7K7OkfFfaZ",
    "Content-Type": "application/octet-stream"
}
HEADERS_TO_SHARE_LINK = {
    "Authorization": "Bearer M6iN1nYzh_YAAAAAAACHmqe-TsJhb-Dur_EB09HNKaguknUwnq2a_PprLOwiSS3W",
    "Content-Type": "application/json"
}


def upload_file(filepath, path_on_dropbox):
    result_upload = upload_to_dropbox(filepath, path_on_dropbox)
    if result_upload:
        return generate_uri(path_on_dropbox)
    else:
        print('Nao foi possivel fazer upload de arquivo')
        return None


def generate_uri(path_on_dbx):
    dbx = dropbox.Dropbox(TOKEN)
    shared_link_metadata = dbx.sharing_create_shared_link_with_settings(path_on_dbx)
    return shared_link_metadata.url


def get_path_on_dropbox(name, type):
    return '/%s/%s' % (type, name)


# def upload_to_dropbox(name, filepath):
#     headers_upload = HEADERS_TO_UPLOAD
#     headers_upload["Dropbox-API-Arg"] = "{\"path\":\"" + name + "\"}"
#     result = None
#     try:
#         with open(filepath, "rb") as audio_file:
#             encoded_file = b64encode(audio_file.read())
#         response = requests.post(URL_UPLOAD, headers=headers_upload, data=encoded_file)
#         result = response.json()
#         print(result)
#         audio_file.close()
#     except (Exception,):
#         print('deu erro com upload file')
#     return result


def upload_to_dropbox(filepath, path_on_dropbox):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    dbx = dropbox.Dropbox(TOKEN)
    path = path_on_dropbox
    with open(filepath, 'rb') as f:
        data = f.read()
    with stopwatch('upload %d bytes' % len(data)):
        try:
            res = dbx.files_upload(data, path)
        except ApiError as err:
            print('*** API error', err)
            return None
    f.close()
    print('uploaded as', res.name.encode('utf8'))
    return res


@contextlib.contextmanager
def stopwatch(message):
    """Context manager to print how long a block of code took."""
    t0 = time.time()
    try:
        yield
    finally:
        t1 = time.time()
        print('Total elapsed time for %s: %.3f' % (message, t1 - t0))


TOKEN = settings.TOKEN_DROPBOX
FOLDER = 'Apps'
SUBFOLDER = 'helpmusician'


def custom_upload_to_dropbox(name, filepath):
    f = open(filepath)
    res = None
    dbx = dropbox.Dropbox(TOKEN)
    file_size = os.path.getsize(filepath)
    path = '/%s' % (name)
    CHUNK_SIZE = 6 * 1024 * 1024
    if file_size <= CHUNK_SIZE:
        res = dbx.files_upload(f.read(), path)
    else:
        upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                   offset=f.tell())
        commit = dropbox.files.CommitInfo(path=path)
        while f.tell() < file_size:
            if ((file_size - f.tell()) <= CHUNK_SIZE):
                res = dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                      cursor,
                                                      commit)
            else:
                dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                cursor.session_id,
                                                cursor.offset)
                cursor.offset = f.tell()

    f.close()
    return res


def download_file(path_ext, path_on_dropbox):
    dbx = dropbox.Dropbox(TOKEN)
    with open(path_ext, "wb") as f:
        metadata, res = dbx.files_download(path=path_on_dropbox)
        f.write(res.content)
    f.close()
    return metadata, res


def delete_file_on_dropbox(path_on_dropbox):
    try:
        dbx = dropbox.Dropbox(TOKEN)
        res = dbx.files_delete_v2(path_on_dropbox)
        return res
    except (Exception,):
        return None
