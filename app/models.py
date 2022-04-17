import os
import uuid
from io import BytesIO

import mutagen
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from picklefield.fields import PickledObjectField

from app.util import get_valid_filename
from app.validators import is_valid_size, is_valid_audio_file, is_valid_youtube
from app.youtubedl import get_meta_info

"""
This module defines Django models.
"""


def source_file_path(instance, filename):
    """
    Get path to source file, using instance ID as subdirectory.

    :param instance: SourceFile instance
    :param filename: File name
    :return: Path to source file
    """
    filename = str(get_valid_filename(filename)).strip()
    return os.path.join(settings.UPLOAD_DIR, str(instance.id), filename)


def mix_track_path(instance, filename):
    """
    Get path to mix track file, using instance ID as subdirectory.

    :param instance: StaticMix/DynamicMix instance
    :param filename: File name
    :return: Path to mix track file
    """
    filename = str(get_valid_filename(filename)).strip()
    return os.path.join(settings.SEPARATE_DIR, str(instance.id), filename)


SPLEETER = 'spleeter'


class TaskStatus(models.IntegerChoices):
    """
    Enum for status of a task.
    """
    QUEUED = 0, 'Queued'
    IN_PROGRESS = 1, 'In Progress'
    DONE = 2, 'Done'
    ERROR = -1, 'Error'


class Bitrate(models.IntegerChoices):
    """
    Enum for MP3 bitrates.
    """
    MP3_192 = 192
    MP3_256 = 256
    MP3_320 = 320


class YTAudioDownloadTask(models.Model):
    """Model representing the status of a task to fetch audio from YouTube link."""
    # UUID to uniquely identify task
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ID of the associated Celery task
    celery_id = models.UUIDField(default=None, null=True, blank=True)
    # Status of task
    status = models.IntegerField(choices=TaskStatus.choices,
                                 default=TaskStatus.QUEUED)
    # Error message in case of error
    error = models.TextField(blank=True)
    # DateTime when upload task completed/failed
    date_finished = models.DateTimeField(default=None, null=True, blank=True)


class SourceFile(models.Model):
    """
    Model representing the file of a source/original audio track.

    If a user uploads the audio file but than aborts the operation, then the SourceFile and the file
    on disk is deleted.
    """
    # UUID to uniquely identify file
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # File object
    file = models.FileField(upload_to=source_file_path,
                            blank=True,
                            null=True,
                            max_length=255,
                            validators=[is_valid_size, is_valid_audio_file])
    public_id = models.CharField(max_length=255, blank=True, null=True)
    duration = models.FloatField(blank=True, null=True)
    # Whether the audio track is from a YouTube link import
    file_url = models.TextField(blank=True, null=True)
    filename = models.TextField(blank=True, null=True)
    path_on_dropbox = models.TextField(blank=True, null=True)
    is_youtube = models.BooleanField(default=False)
    # The original YouTube link, if source is from YouTube
    youtube_link = models.URLField(unique=True,
                                   blank=True,
                                   null=True,
                                   validators=[is_valid_youtube])
    # If file is from a YouTube link import, then this field refers to the task executed to download the audio file.
    youtube_fetch_task = models.OneToOneField(YTAudioDownloadTask,
                                              on_delete=models.CASCADE,
                                              null=True,
                                              blank=True)

    def metadata(self):
        """Extract artist and title information from audio

        :return: Dict containing 'artist' and 'title' fields associated with the track
        """
        artist = ''
        title = ''
        if self.youtube_link:
            try:
                info = get_meta_info(self.youtube_link)
            except:
                print('Getting metadata failed')
                info = None
            if not info:
                artist = ''
                title = ''
            elif info['embedded_artist'] and info['embedded_title']:
                artist = info['embedded_artist']
                title = info['embedded_title']
            elif info['parsed_artist'] and info['parsed_title']:
                artist = info['parsed_artist']
                title = info['parsed_title']
            else:
                artist = info['uploader']
                title = info['title']
        else:
            try:
                if settings.DEFAULT_FILE_STORAGE == 'app.storage.FileSystemStorage':
                    audio = EasyID3(self.file.path) if self.file.path.endswith('mp3') else mutagen.File(self.file.path)
                else:
                    r = requests.get(self.file.url)
                    file = BytesIO(r.content)
                    audio = EasyID3(file) if self.file.url.endswith('mp3') else mutagen.File(file)

                if 'artist' in audio:
                    artist = audio['artist'][0]
                if 'title' in audio:
                    title = audio['title'][0]
            except ID3NoHeaderError:
                pass
            except:
                pass
        return (str(get_valid_filename(artist)), str(get_valid_filename(title)))

    def __str__(self):
        if self.youtube_link:
            return self.youtube_link
        elif self.file and self.file.name:
            return os.path.basename(self.file.name)
        else:
            return self.id


class SourceTrack(models.Model):
    """
    Model representing the source song itself. SourceTrack differs from SourceFile as SourceTrack
    contains additional metadata such as artist, title, and date created info.

    SourceTrack contains a reference to SourceFile. The reasoning why they're separate is because the
    user first uploads an audio file to the server, then confirms the artist and title information,
    then completes the process of adding a new audio track.

    If a user uploads the audio file but than aborts the operation, then the SourceFile and the file
    on disk is deleted.

    TODO: Refactor SourceFile and SourceTrack in a cleaner way.
    """
    # UUID to uniquely identify the source song
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    # Corresponding SourceFile (id)
    source_file = models.ForeignKey(SourceFile, blank=True, null=True, on_delete=models.CASCADE)
    # Artist name
    artist = models.CharField(max_length=200)
    thumb = models.URLField(blank=True, null=True)
    # Title
    title = models.CharField(max_length=200)
    # DateTime when user added the song
    date_created = models.DateTimeField(auto_now_add=True)

    tone = models.CharField(max_length=10, blank=True, null=True)
    bpm = models.CharField(max_length=10, blank=True, null=True)
    bar_length = models.CharField(max_length=10, blank=True, null=True)
    chords = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def url(self):
        """Get the URL of the source file."""
        if self.source_file.file_url:
            return self.source_file.file_url
        return ''

    def youtube_link(self):
        """Get the YouTube link of the source file (may return None)."""
        return self.source_file.youtube_link

    def youtube_fetch_task(self):
        """Get the ID of the YouTube fetch task associated with the track."""
        return self.source_file.youtube_fetch_task.id

    def __str__(self):
        """String representation."""
        return self.artist + '-' + self.title


# pylint: disable=unsubscriptable-object
class StaticMix(models.Model):
    """Model representing a statically mixed track (certain parts are excluded)."""
    # UUID to uniquely identify track
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ID of the associated Celery task
    celery_id = models.UUIDField(default=None, null=True, blank=True)
    # Separation model
    separator = models.CharField(max_length=20,
                                 default=SPLEETER)
    # Separator-specific args
    separator_args = PickledObjectField(default=dict)
    # Bitrate
    bitrate = models.IntegerField(choices=Bitrate.choices,
                                  default=Bitrate.MP3_256)
    # Source track on which it is based
    source_track = models.ForeignKey(SourceTrack,
                                     related_name='static',
                                     on_delete=models.CASCADE)
    # Whether track contains vocals
    vocals = models.BooleanField()
    # Whether track contains vocals
    piano = models.BooleanField()
    # Whether track contains drums
    drums = models.BooleanField()
    # Whether track contains bass
    bass = models.BooleanField()
    # Whether track contains accompaniment ('other' is the term used by Spleeter API)
    other = models.BooleanField()
    # Status of source separation task
    status = models.IntegerField(choices=TaskStatus.choices,
                                 default=TaskStatus.QUEUED)
    public_id = models.CharField(max_length=255, blank=True, null=True)
    duration = models.FloatField(blank=True, null=True)
    # Underlying file
    file = models.FileField(upload_to=mix_track_path,
                            max_length=255,
                            blank=True)
    file_url = models.TextField(blank=True, null=True)
    filename = models.TextField(blank=True, null=True)
    path_on_dropbox = models.TextField(blank=True, null=True)
    # Error message
    error = models.TextField(blank=True)
    # DateTime when source separation task was started
    date_created = models.DateTimeField(auto_now_add=True)
    # DateTime when source separation task completed/failed
    date_finished = models.DateTimeField(default=None, null=True, blank=True)

    def artist(self):
        """Get the artist name."""
        return self.source_track.artist

    def title(self):
        """Get the title."""
        return self.source_track.title

    def url(self):
        """Get the file URL"""
        if self.file_url:
            return self.file_url
        return ''

    def formatted_name(self):
        """
        Produce a string with the format like:
        "Artist - Title (vocals, drums, bass, other)"
        """
        prefix_lst = [self.source_track.artist, '-', self.source_track.title]
        parts_lst = []
        if self.vocals:
            parts_lst.append('vocals')
        if self.piano:
            parts_lst.append('piano')
        if self.drums:
            parts_lst.append('drums')
        if self.bass:
            parts_lst.append('bass')
        if self.other:
            parts_lst.append('other')
        prefix = ''.join(prefix_lst)
        parts = '_'.join(parts_lst)

        suffix = f'{self.bitrate}kbps_{self.separator}'
        return f'{prefix}_{parts}__{suffix}_'

    def source_path(self):
        """Get the path to the source file."""
        return str(self.source_track.source_file.file_url)

    def source_url(self):
        """Get the URL of the source file."""
        return self.source_track.source_file.file_url

    def get_extra_info(self):
        """Get extra information about the mix"""
        return [f'{self.bitrate}kbps', '(24 kHz)']

    class Meta:
        unique_together = [[
            'source_track', 'separator', 'separator_args', 'bitrate', 'vocals', 'piano', 'drums',
            'bass', 'other'
        ]]


# pylint: disable=unsubscriptable-object
class DynamicMix(models.Model):
    """Model representing a track that has been split into individually components."""
    # UUID to uniquely identify track
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ID of the associated Celery task
    celery_id = models.UUIDField(default=None, null=True, blank=True)
    # Separation model
    separator = models.CharField(max_length=20,
                                 default=SPLEETER)
    # Separator-specific args
    separator_args = PickledObjectField(default=dict)
    # Bitrate
    bitrate = models.IntegerField(choices=Bitrate.choices,
                                  default=Bitrate.MP3_256)
    # Source track on which it is based
    source_track = models.ForeignKey(SourceTrack,
                                     related_name='dynamic',
                                     on_delete=models.CASCADE)

    folder_path_on_dropbox = models.TextField(blank=True, null=True)
    # Path to vocals file
    vocals_file = models.FileField(upload_to=mix_track_path,
                                   max_length=255,
                                   blank=True)
    vocals_url = models.TextField(blank=True, null=True)
    vocals_path = models.TextField(blank=True, null=True)
    vocals_public_id = models.CharField(max_length=255, blank=True, null=True)
    vocals_duration = models.FloatField(blank=True, null=True)

    # Path to piano file
    piano_file = models.FileField(upload_to=mix_track_path,
                                  max_length=255,
                                  blank=True)
    piano_url = models.TextField(blank=True, null=True)
    piano_path = models.TextField(blank=True, null=True)
    piano_public_id = models.CharField(max_length=255, blank=True, null=True)
    piano_duration = models.FloatField(blank=True, null=True)

    # Path to accompaniment file
    other_file = models.FileField(upload_to=mix_track_path,
                                  max_length=255,
                                  blank=True)
    other_url = models.TextField(blank=True, null=True)
    other_path = models.TextField(blank=True, null=True)
    other_public_id = models.CharField(max_length=255, blank=True, null=True)
    other_duration = models.FloatField(blank=True, null=True)

    # Path to bass file
    bass_file = models.FileField(upload_to=mix_track_path,
                                 max_length=255,
                                 blank=True)
    bass_url = models.TextField(blank=True, null=True)
    bass_path = models.TextField(blank=True, null=True)
    bass_public_id = models.CharField(max_length=255, blank=True, null=True)
    bass_duration = models.FloatField(blank=True, null=True)

    # Path to drums file
    drums_file = models.FileField(upload_to=mix_track_path,
                                  max_length=255,
                                  blank=True)
    drums_url = models.TextField(blank=True, null=True)
    drums_path = models.TextField(blank=True, null=True)
    drums_public_id = models.CharField(max_length=255, blank=True, null=True)
    drums_duration = models.FloatField(blank=True, null=True)
    # Status of source separation task
    status = models.IntegerField(choices=TaskStatus.choices,
                                 default=TaskStatus.QUEUED)
    # Error message
    error = models.TextField(blank=True)
    # DateTime when source separation task was started
    date_created = models.DateTimeField(auto_now_add=True)
    # DateTime when source separation task completed/failed
    date_finished = models.DateTimeField(default=None, null=True, blank=True)

    def tone(self):
        """Get the artist name."""
        return self.source_track.tone

    def bpm(self):
        """Get the artist name."""
        return self.source_track.bpm

    def bar_length(self):
        """Get the artist name."""
        return self.source_track.bar_length

    def chords(self):
        """Get the artist name."""
        return self.source_track.chords

    def notes(self):
        """Get the artist name."""
        return self.source_track.notes

    def artist(self):
        """Get the artist name."""
        return self.source_track.artist

    def title(self):
        """Get the title."""
        return self.source_track.title

    def formatted_prefix(self):
        """
        Produce a string with the format like:
        "Artist - Title"
        """
        return f'{self.source_track.artist}-{self.source_track.title}'

    def formatted_suffix(self):
        """
        Produce a string describing the separator model and random shift value:
        "[Demucs, 0]"
        """
        return f'({self.bitrate}kbps_{self.separator})'

    def get_realpath_file(self, file_path):
        return settings.SERVER_URL + file_path

    def source_path(self):
        """Get the path to the source file."""
        return self.source_track.source_file.file_url

    def source_url(self):
        """Get the URL of the source file."""
        return self.source_track.source_file.file_url

    def get_extra_info(self):
        """Get extra information about the mix"""
        return [f'{self.bitrate}kbps', '(24 kHz)']

    class Meta:
        unique_together = [[
            'source_track',
            'separator',
            'separator_args',
            'bitrate'
        ]]
