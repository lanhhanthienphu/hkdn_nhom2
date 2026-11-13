"""Local ticket storage with no public URL."""

import os
from pathlib import PurePosixPath
from uuid import uuid4

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateAttachmentStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(file_permissions_mode=0o600, directory_permissions_mode=0o700)

    @property
    def base_location(self):
        return settings.PRIVATE_ATTACHMENT_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise ValueError('Ticket attachments have no public URL. Use tickets:attachment_download.')


def attachment_upload_path(instance, filename):
    extension = PurePosixPath(filename.replace('\\', '/')).suffix.lower()
    return f'tickets/{instance.ticket_id}/{uuid4().hex}{extension}'
