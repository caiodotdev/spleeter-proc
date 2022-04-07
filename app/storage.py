from django.core.files.storage import \
    FileSystemStorage as BaseFileSystemStorage
from django.utils.deconstruct import deconstructible

from .util import get_valid_filename

"""
Simple wrappers of the base storage backends except that characters like spaces, commas, brackets
are allowed in the filename.
"""


@deconstructible
class FileSystemStorage(BaseFileSystemStorage):
    def get_valid_name(self, name):
        return get_valid_filename(name)
