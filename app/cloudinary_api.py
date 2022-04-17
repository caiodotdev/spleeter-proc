import os.path

import cloudinary
import cloudinary.uploader
import cloudinary.api

from django.conf import settings

CLOUD_NAME = settings.CLOUDINARY_CLOUD_NAME
API_KEY = settings.CLOUDINARY_API_KEY
API_SECRET = settings.CLOUDINARY_API_SECRET
import requests

# CLOUD_NAME = 'freelancerinc'
# API_KEY = '977733565746842'
# API_SECRET = 'q552mjrVeEmgPs1kUxfKzp4wz2o'

cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET,
    secure=True
)


def upload_audio(file_path, folder):
    return cloudinary.uploader.upload(file_path,
                                      resource_type="video",
                                      public_id=folder)


def remove_cloudinary_file(public_id):
    req = cloudinary.uploader.destroy(public_id, resource_type="video")
    if req['result'] != 'ok':
        print('Erro ao remover arquivo')
    print('Arquivo removido da cloudinary com sucesso')


def download_file(path_ext, url):
    response = requests.get(url)
    open(path_ext, "wb").write(response.content)

