"""Adapt persisted Ticket events to the existing after-commit email service."""

import logging
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.urls import reverse

from .services import EVENTS, notify_ticket_after_commit

logger = logging.getLogger(__name__)


def _ticket_url(ticket):
    # Use a configured origin, never the request Host or a submitted URL.
    origin = settings.HELPDESK_BASE_URL
    if not isinstance(origin, str):
        raise ValidationError('HELPDESK_BASE_URL phải là URL HTTP/HTTPS của hệ thống.')
    origin = origin.strip().rstrip('/')
    URLValidator(schemes=['http', 'https'])(origin)
    try:
        parts = urlsplit(origin)
        if parts.username is not None or parts.password is not None or parts.path or '?' in origin or '#' in origin:
            raise ValidationError('HELPDESK_BASE_URL chỉ gồm giao thức, tên miền và cổng nếu có.')
    except ValueError as error:
        raise ValidationError('HELPDESK_BASE_URL không hợp lệ.') from error
    return origin + reverse('tickets:detail', args=[ticket.pk])


def notify_ticket_event(ticket, event):
    """Schedule an event from server-side user data; return False if skipped.

    Call inside the transaction that saved the event. Invalid email/configuration
    is logged without undoing a valid ticket. Delivery failures are handled by
    notify_ticket_after_commit (robust=True), not by a retry queue.
    """
    if event not in EVENTS:
        raise ValueError('Unknown ticket notification event.')
    if not ticket.pk or ticket._state.adding:
        raise ValueError('Save the ticket before scheduling its notification.')

    recipient = ticket.assigned_to if event == 'assigned' else ticket.created_by
    if recipient is None or not recipient.is_active or not recipient.email.strip():
        logger.info('Skipped %s notification for ticket %s: no active recipient with email.', event, ticket.pk)
        return False

    try:
        notify_ticket_after_commit(
            database=ticket._state.db or 'default',
            event=event,
            ticket_code=ticket.code,
            title=ticket.title,
            to_email=recipient.email,
            ticket_url=_ticket_url(ticket),
            recipient_name=recipient.get_full_name() or recipient.get_username(),
            assignee_name=ticket.assignee_name,
            status_label=ticket.status_label,
        )
    except ValidationError as error:
        logger.warning('Skipped %s notification for ticket %s: %s', event, ticket.pk, '; '.join(error.messages))
        return False
    return True
