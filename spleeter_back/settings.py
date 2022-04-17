import os
from datetime import timedelta
from multiprocessing import cpu_count

# SECURITY WARNING: don't run with debug turned on in production!
from celery.schedules import crontab

DEBUG = True

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.getenv('SECRET_KEY', 'sekrit')

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', 'AIzaSyB9Q-CYO0UvW7V0rp7Vep_yz3PBGuNlzc8')

CPU_SEPARATION = bool(int(os.getenv('CPU_SEPARATION', '1')))

ALLOWED_HOSTS = [os.getenv('APP_HOST'), '0.0.0.0', '127.0.0.1', 'localhost', '*']

DEFAULT_FILE_STORAGE = os.getenv('DEFAULT_FILE_STORAGE', 'api.storage.FileSystemStorage')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SELERLIZER = 'json'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BEAT_SCHEDULE = {
    'check-dynamic-queue-every-minute': {
        'task': 'app.tasks.check_dynamic_queue',
        'schedule': crontab(minute="*/5"),
    },
    'clean-every-minute': {
        'task': 'app.tasks.clean_tasks_results',
        'schedule': crontab(minute="*/15"),
    },
}

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': '../spleeter-front/spleeter-web.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'd3163uulbn6jdh',
        'USER': 'yercjzhnbfqlpi',
        'PASSWORD': '67635ed4d5a5cb1a61142227b8ab1c19627bda30208ad2853dc0c16144cae45e',
        'HOST': 'ec2-52-3-60-53.compute-1.amazonaws.com',
        'PORT': '5432',
    }
}

import dj_database_url

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

MEDIA_ROOT = 'media'
MEDIA_URL = '/media/'
SEPARATE_DIR = 'separate'
UPLOAD_DIR = 'uploads'

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

VALID_MIME_TYPES = [
    'audio/aac', 'audio/aiff', 'audio/x-aiff', 'audio/ogg', 'video/ogg', 'application/ogg', 'audio/opus',
    'audio/vorbis', 'audio/mpeg',
    'audio/mp3', 'audio/mpeg3', 'audio/x-mpeg-3', 'video/mpeg', 'audio/m4a', 'audio/x-m4a', 'audio/x-hx-aac-adts',
    'audio/mp4', 'video/x-mpeg',
    'audio/flac', 'audio/x-flac', 'audio/wav', 'audio/x-wav', 'audio/webm', 'video/webm'
]

VALID_FILE_EXT = [
    # Lossless
    '.aif',
    '.aifc',
    '.aiff',
    '.flac',
    '.wav',
    # Lossy
    '.aac',
    '.m4a',
    '.mp3',
    '.opus',
    '.weba',
    '.webm',
    # Ogg (Lossy)
    '.ogg',
    '.oga',
    '.mogg'
]

UPLOAD_FILE_SIZE_LIMIT = 100 * 1024 * 1024
YOUTUBE_LENGTH_LIMIT = 30 * 60
YOUTUBE_MAX_RETRIES = 3

# Application definition
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app.apps.AppConfig',
    'rest_framework',
    'knox',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'cloudinary',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'spleeter_back.urls'

SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:8000')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'spleeter_back.wsgi.application'

CORS_ALLOW_ALL_ORIGINS = True  # If this is used then `CORS_ALLOWED_ORIGINS` will not have any effect
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_ORIGIN_WHITELIST = (
    'http://localhost:8000',
    'http://localhost:8080',
)

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    # os.path.join(BASE_DIR, 'static'),
]

SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework.authentication.BasicAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
        'knox.auth.TokenAuthentication',
    ]
}

from rest_framework.settings import api_settings

REST_KNOX = {
    'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': timedelta(days=7),
    'USER_SERIALIZER': 'app.serializers.CustomUserSerializer',
    'TOKEN_LIMIT_PER_USER': None,
    'AUTO_REFRESH': False,
    'EXPIRY_DATETIME_FORMAT': api_settings.DATETIME_FORMAT
}

API_KEY_DROPBOX = os.getenv('API_KEY_DROPBOX', 'M6iN1nYzh_YAAAAAAACUfhWR5kFUT-4Hwak6aAwSANv5vP0tLCHmnHCi37y9acqY')
TOKEN_DROPBOX = os.getenv('TOKEN_DROPBOX', 'M6iN1nYzh_YAAAAAAACUfhWR5kFUT-4Hwak6aAwSANv5vP0tLCHmnHCi37y9acqY')

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', 'cloudinary://977733565746842:q552mjrVeEmgPs1kUxfKzp4wz2o@freelancerinc')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY',
                               '977733565746842')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET',
                                  'q552mjrVeEmgPs1kUxfKzp4wz2o')
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME',
                                  'freelancerinc')
