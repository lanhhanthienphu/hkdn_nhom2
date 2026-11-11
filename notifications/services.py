from functools import partial

from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.validators import URLValidator, validate_email
from django.db import transaction
from django.template.loader import render_to_string


EVENTS = {
    "created": "Đã tiếp nhận yêu cầu",
    "assigned": "Được phân công xử lý",
    "resolved": "Yêu cầu đã được giải quyết",
}


def _text(value, label, *, required=False):
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"{label} phải là chuỗi.")
    value = " ".join(value.split())
    if required and not value:
        raise ValidationError(f"Vui lòng cung cấp {label.lower()}.")
    return value


def build_ticket_email(
    *,
    event,
    ticket_code,
    title,
    to_email,
    ticket_url,
    recipient_name="",
    assignee_name="",
    status_label="",
):
    """Build an email from plain values; no Ticket model or delivery is required."""
    if not isinstance(event, str) or event not in EVENTS:
        raise ValidationError("Loại thông báo không hợp lệ.")

    ticket_code = _text(ticket_code, "Mã ticket", required=True)
    title = _text(title, "Tiêu đề", required=True)
    to_email = _text(to_email, "Email người nhận", required=True)
    ticket_url = _text(ticket_url, "Đường dẫn ticket", required=True)
    validate_email(to_email)
    URLValidator(schemes=["http", "https"])(ticket_url)

    context = {
        "heading": EVENTS[event],
        "ticket_code": ticket_code,
        "title": title,
        "ticket_url": ticket_url,
        "recipient_name": _text(recipient_name, "Tên người nhận") or "bạn",
        "assignee_name": _text(assignee_name, "Tên kỹ thuật viên"),
        "status_label": _text(status_label, "Trạng thái"),
    }
    message = EmailMultiAlternatives(
        subject=f"[Helpdesk {ticket_code}] {EVENTS[event]}: {title}",
        body=render_to_string(f"notifications/{event}.txt", context),
        to=[to_email],
    )
    message.attach_alternative(
        render_to_string(f"notifications/{event}.html", context),
        "text/html",
    )
    return message


def send_ticket_notification(*, mailer="default", **notification):
    """Send using the configured Django mailer and return its sent count."""
    return build_ticket_email(**notification).send(using=mailer)


def notify_ticket_after_commit(*, database="default", mailer="default", **notification):
    """Validate now, then deliver only after a successful database commit.

    With no open transaction, Django executes the callback immediately.
    Delivery errors are logged by Django (robust=True); this is not a retry queue.
    """
    message = build_ticket_email(**notification)
    transaction.on_commit(
        partial(message.send, using=mailer),
        using=database,
        robust=True,
    )
