"""Remove physical files only after their database deletion commits."""

from functools import partial

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Attachment


@receiver(post_delete, sender=Attachment)
def delete_committed_attachment_file(sender, instance, using, **kwargs):
    if instance.file.name:
        transaction.on_commit(
            partial(instance.file.storage.delete, instance.file.name), using=using, robust=True,
        )
