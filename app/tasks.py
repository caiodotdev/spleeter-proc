import os
import os.path
import pathlib
import shutil
from typing import Dict

from billiard.exceptions import SoftTimeLimitExceeded
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django_celery_results.models import TaskResult

from .celery import app
from .cloudinary_api import download_file, upload_audio
from .models import (DynamicMix, StaticMix, TaskStatus)
from .separators.spleeter_separator import SpleeterSeparator
from .util import get_valid_filename

"""
This module defines various Celery tasks used for Spleeter Web.
"""


def get_separator(separator: str, separator_args: Dict, bitrate: int, cpu_separation: bool):
    return SpleeterSeparator(cpu_separation, bitrate)


@shared_task()
def check_static_queue():
    queue = StaticMix.objects.filter(status=TaskStatus.QUEUED)
    if queue.exists():
        print('Em fila Static ', queue.count())
        selected = queue.first()
        selected.status = TaskStatus.IN_PROGRESS
        selected.save()
        result = static_mix_processing.delay(selected.pk)
        selected.celery_id = result.id
        selected.save()


@shared_task()
def check_dynamic_queue():
    queue_dynamic = DynamicMix.objects.filter(status=TaskStatus.QUEUED)
    if queue_dynamic.exists():
        print('Em fila Dynamic ', queue_dynamic.count())
        selected = queue_dynamic.first()
        selected.status = TaskStatus.IN_PROGRESS
        selected.save()
        result = dynamic_mix_processing.delay(selected.pk)
        selected.celery_id = result.id
        selected.save()


@app.task()
def static_mix_processing(static_mix_id):
    static_mix = StaticMix.objects.get(pk=static_mix_id)
    try:
        # Get paths
        print('processing static mix ', static_mix_id)
        directory = os.path.join(settings.MEDIA_ROOT, settings.SEPARATE_DIR,
                                 static_mix_id)
        filename = str(get_valid_filename(static_mix.formatted_name()) + '.mp3').strip()
        rel_media_path = os.path.join(settings.SEPARATE_DIR, static_mix_id,
                                      filename)
        rel_path = os.path.join(settings.MEDIA_ROOT, rel_media_path)
        rel_path_dir = os.path.join(settings.MEDIA_ROOT, settings.SEPARATE_DIR,
                                    static_mix_id)

        directory_file_original = os.path.join(settings.MEDIA_ROOT, settings.SEPARATE_DIR,
                                               static_mix_id, 'upload')
        path_original = os.path.join(directory_file_original,
                                     static_mix.source_track.source_file.filename)

        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
        pathlib.Path(directory_file_original).mkdir(parents=True, exist_ok=True)
        separator = get_separator(static_mix.separator,
                                  static_mix.separator_args,
                                  static_mix.bitrate, settings.CPU_SEPARATION)

        parts = {
            'vocals': static_mix.vocals,
            'piano': static_mix.piano,
            'drums': static_mix.drums,
            'bass': static_mix.bass,
            'other': static_mix.other
        }

        # Download music original to directory created (media/separated/id/upload/)
        download_file(path_original, static_mix.source_track.source_file.file_url)
        # metadata, res = download_file(path_original, static_mix.source_track.source_file.path_on_dropbox)
        # Criar Static Mix na pasta (/media/separate/id/)
        if os.path.exists(path_original):
            separator.create_static_mix(parts, path_original, rel_path)

        # Check file exists
        if os.path.exists(rel_path):
            # Upload to Dropbox da Static Mix
            # path_on_dropbox = get_path_on_dropbox(filename, 'static_mix')
            # file_url = upload_file(rel_path, path_on_dropbox)
            path_on_cloudinary = 'static' + '/' + filename
            req = upload_audio(rel_path, path_on_cloudinary)
            static_mix.status = TaskStatus.DONE
            static_mix.date_finished = timezone.now()
            # static_mix.file_url = make_url(file_url)
            static_mix.file_url = req['secure_url']
            static_mix.public_id = req['public_id']
            static_mix.duration = req['duration']
            static_mix.filename = filename
            # static_mix.path_on_dropbox = path_on_dropbox
            static_mix.save()
            print('Dropbox on ', static_mix.path_on_dropbox)
            # Remove Folders
            os.remove(rel_path)
            shutil.rmtree(rel_path_dir, ignore_errors=True)
        else:
            raise Exception('Error writing to file')
    except FileNotFoundError as error:
        print(error)
        print('Please make sure you have FFmpeg and FFprobe installed.')
        static_mix.status = TaskStatus.ERROR
        static_mix.date_finished = timezone.now()
        static_mix.error = str(error)
        static_mix.save()
    except SoftTimeLimitExceeded:
        print('Aborted!')
    except Exception as error:
        print(error)
        static_mix.status = TaskStatus.ERROR
        static_mix.date_finished = timezone.now()
        static_mix.error = str(error)
        static_mix.save()


@app.task()
def dynamic_mix_processing(dynamic_mix_id):
    dynamic_mix = DynamicMix.objects.get(pk=dynamic_mix_id)
    try:
        # Get paths
        print('processing dynamicmix ', dynamic_mix_id)
        directory = os.path.join(settings.MEDIA_ROOT, settings.SEPARATE_DIR,
                                 dynamic_mix_id)
        rel_media_path = os.path.join(settings.SEPARATE_DIR, dynamic_mix_id)
        file_prefix = get_valid_filename(dynamic_mix.formatted_prefix())
        file_suffix = get_valid_filename(dynamic_mix.formatted_suffix())
        rel_path = os.path.join(settings.MEDIA_ROOT, rel_media_path)

        directory_file_original = os.path.join(settings.MEDIA_ROOT, settings.SEPARATE_DIR,
                                               dynamic_mix_id, 'upload')
        path_original = os.path.join(directory_file_original,
                                     dynamic_mix.source_track.source_file.filename)

        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
        pathlib.Path(directory_file_original).mkdir(parents=True, exist_ok=True)

        separator = get_separator(dynamic_mix.separator,
                                  dynamic_mix.separator_args,
                                  dynamic_mix.bitrate,
                                  settings.CPU_SEPARATION)

        # Download music original to directory created (media/separated/id/upload/)
        # metadata, res = download_file(path_original, dynamic_mix.source_track.source_file.path_on_dropbox)
        download_file(path_original, dynamic_mix.source_track.source_file.file_url)
        # Criar Static Mix na pasta (/media/separate/id/)
        if os.path.exists(path_original):
            separator.separate_into_parts(path_original, rel_path)

        # Check all parts exist
        if exists_all_parts(rel_path):
            rename_all_parts(rel_path, file_prefix, file_suffix)
            upload_all_parts(directory, dynamic_mix, rel_path, file_prefix, file_suffix)
            dynamic_mix.status = TaskStatus.DONE
            dynamic_mix.date_finished = timezone.now()
            dynamic_mix.save()
        else:
            raise Exception('Error writing to file')
    except FileNotFoundError as error:
        print(error)
        print('Please make sure you have FFmpeg and FFprobe installed.')
        dynamic_mix.status = TaskStatus.ERROR
        dynamic_mix.date_finished = timezone.now()
        dynamic_mix.error = str(error)
        dynamic_mix.save()
    except SoftTimeLimitExceeded:
        print('Aborted!')
    except Exception as error:
        print(error)
        dynamic_mix.status = TaskStatus.ERROR
        dynamic_mix.date_finished = timezone.now()
        dynamic_mix.error = str(error)
        dynamic_mix.save()


def exists_all_parts(rel_path):
    """Returns whether all of the individual component tracks exist on filesystem."""
    parts = ['vocals', 'piano', 'other', 'bass', 'drums']
    for part in parts:
        rel_part_path = os.path.join(rel_path, f'{part}.mp3')
        if not os.path.exists(rel_part_path):
            print(f'{rel_part_path} does not exist')
            return False
    return True


def rename_all_parts(rel_path, file_prefix: str, file_suffix: str):
    """Renames individual part files to names with track artist and title."""
    parts = ['vocals', 'piano', 'other', 'bass', 'drums']
    for part in parts:
        old_rel_path = os.path.join(rel_path, f'{part}.mp3')
        new_rel_path = os.path.join(
            rel_path, f'{file_prefix}_{part}_{file_suffix}.mp3')
        print(f'Renaming {old_rel_path} to {new_rel_path}')
        os.rename(old_rel_path, new_rel_path)


def upload_all_parts(directory, dynamic_mix, rel_path, file_prefix: str, file_suffix: str):
    filenames = {
        'vocals': f'{file_prefix}_vocals_{file_suffix}.mp3',
        'piano': f'{file_prefix}_piano_{file_suffix}.mp3',
        'other': f'{file_prefix}_other_{file_suffix}.mp3',
        'bass': f'{file_prefix}_bass_{file_suffix}.mp3',
        'drums': f'{file_prefix}_drums_{file_suffix}.mp3'
    }
    for part in filenames.keys():
        filename = filenames[part]
        path_on_cloudinary = 'dynamic' + '/' + file_prefix + '/' + filename
        part_file_path = os.path.join(rel_path, filename)
        print(f'Upload part {part}: {part_file_path}')
        req = upload_audio(part_file_path, path_on_cloudinary)
        if part == 'vocals':
            dynamic_mix.vocals_url = req['secure_url']
            dynamic_mix.vocals_public_id = req['public_id']
            dynamic_mix.vocals_duration = req['duration']
        elif part == 'piano':
            dynamic_mix.piano_url = req['url']
            dynamic_mix.piano_public_id = req['public_id']
            dynamic_mix.piano_duration = req['duration']
        elif part == 'bass':
            dynamic_mix.bass_url = req['url']
            dynamic_mix.bass_public_id = req['public_id']
            dynamic_mix.bass_duration = req['duration']
        elif part == 'drums':
            dynamic_mix.drums_url = req['url']
            dynamic_mix.drums_public_id = req['public_id']
            dynamic_mix.drums_duration = req['duration']
        else:
            dynamic_mix.other_url = req['url']
            dynamic_mix.other_public_id = req['public_id']
            dynamic_mix.other_duration = req['duration']
    shutil.rmtree(directory, ignore_errors=True)


@shared_task()
def clean_tasks_results():
    qs = TaskResult.objects.all()
    print('---- Clean all Results')
    qs.delete()
    print('---- Clean all Results - Done')
