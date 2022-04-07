import os
import shutil

from django.conf import settings
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from .dropbox_uploader.core import delete_file_on_dropbox
from .models import DynamicMix, SourceFile, SourceTrack, StaticMix

"""
This module defines pre- and post-delete signals to ensure files are deleted when a model is deleted from the DB.
"""


@receiver(pre_delete,
          sender=SourceFile,
          dispatch_uid='delete_source_file_signal')
def delete_source_file(sender, instance, using, **kwargs):
    """Pre-delete signal to delete source file on disk before deleting instance."""
    if instance.file:
        instance.file.delete()

    # Delete directory
    if str(instance.id):
        directory = os.path.join(settings.MEDIA_ROOT, settings.UPLOAD_DIR,
                                 str(instance.id))
        shutil.rmtree(directory, ignore_errors=True)
        print('Removed directory: ', directory)
        delete_file_on_dropbox(instance.path_on_dropbox)

    if instance.youtube_fetch_task:
        instance.youtube_fetch_task.delete()


@receiver(post_delete,
          sender=SourceTrack,
          dispatch_uid='delete_source_track_signal')
def delete_source_track(sender, instance, using, **kwargs):
    """Post-delete signal to source track file on disk before deleting instance."""
    if instance.source_file:
        # This will call delete_source_file above
        instance.source_file.delete()
        delete_file_on_dropbox(instance.source_file.path_on_dropbox)


@receiver(pre_delete,
          sender=StaticMix,
          dispatch_uid='delete_static_mix_signal')
def delete_static_mix(sender, instance, using, **kwargs):
    """
    Pre-delete signal to static mix file on disk before deleting instance.

    Cannot be post-delete or else submitting a separation task with 'overwrite' flag does
    not work.
    """
    if instance.file:
        instance.file.delete()

    # Delete directory
    if str(instance.id):
        directory = os.path.join(settings.MEDIA_ROOT, settings.SEPARATE_DIR,
                                 str(instance.id))
        shutil.rmtree(directory, ignore_errors=True)
        print('Removed directory: ', directory)
        delete_file_on_dropbox(instance.path_on_dropbox)


@receiver(pre_delete,
          sender=DynamicMix,
          dispatch_uid='delete_dynamic_mix_signal')
def delete_dynamic_mix(sender, instance, using, **kwargs):
    if instance.vocals_url:
        delete_file_on_dropbox(instance.vocals_path)
        delete_file_on_dropbox(instance.piano_path)
        delete_file_on_dropbox(instance.other_path)
        delete_file_on_dropbox(instance.drums_path)
        delete_file_on_dropbox(instance.bass_path)
        delete_file_on_dropbox(instance.folder_path_on_dropbox)

    # Delete directory
    if str(instance.id):
        directory = os.path.join(settings.MEDIA_ROOT, settings.SEPARATE_DIR,
                                 str(instance.id))
        shutil.rmtree(directory, ignore_errors=True)
        print('Removed directory: ', directory)
