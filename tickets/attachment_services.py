"""Create a real ticket and its optional file as one application operation."""

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from notifications.ticket_events import notify_ticket_event

from .attachment_validators import validate_attachment
from .models import Attachment, Ticket, TicketHistory

logger = logging.getLogger(__name__)


def _display_name(upload):
    name = upload.name.replace('\\', '/').rsplit('/', 1)[-1]
    name = ''.join(character for character in name if character.isprintable()).strip()
    if not name or len(name) > 255:
        raise ValidationError('Tên tệp không hợp lệ.', code='attachment_name')
    return name


def create_ticket_with_attachment(*, author, data):
    """Accept validated TicketForm data; revalidate file bytes before storage.

    This owns the outer transaction (durable=True). Call outside another atomic
    block so a later outer rollback cannot leave a file without its database row.
    Django TestCase's isolation transaction is intentionally supported by Django.
    """
    if not author.is_authenticated or not author.is_active:
        raise PermissionDenied

    upload = data.get('attachment')
    if upload:
        validate_attachment(upload)
        original_name = _display_name(upload)

    stored_file = None
    try:
        with transaction.atomic(durable=True):
            ticket = Ticket.objects.create(
                **{key: data[key] for key in ('title', 'category', 'priority', 'location', 'description')},
                created_by=author,
                status='new',
            )
            if upload:
                attachment = Attachment(ticket=ticket, uploaded_by=author, original_name=original_name)
                upload.seek(0)
                attachment.file.save(original_name, upload, save=False)
                stored_file = (attachment.file.storage, attachment.file.name)
                attachment.size = attachment.file.size
                attachment.save()
                # Retain BE1's metadata interface for existing templates/integrations.
                ticket.attachment_name = original_name
                ticket.attachment_size = attachment.size
                ticket.save(update_fields=['attachment_name', 'attachment_size'])

            TicketHistory.objects.create(
                ticket=ticket, changed_by=author, old_status='', new_status='new',
                note='Đã tạo yêu cầu hỗ trợ sự cố',
            )
            notify_ticket_event(ticket, 'created')
        return ticket
    except Exception:
        # A filesystem write is not rolled back by a database transaction.
        if stored_file:
            storage, name = stored_file
            try:
                storage.delete(name)
            except Exception:
                logger.exception('Could not clean up attachment after failed ticket creation: %s', name)
        raise
