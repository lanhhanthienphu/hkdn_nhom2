from io import StringIO
from pathlib import Path
from smtplib import SMTPException
from tempfile import TemporaryDirectory

from django.core import mail
from django.core.exceptions import ValidationError
from django.core.mail.backends.base import BaseEmailBackend
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase, override_settings

from .services import (
    build_ticket_email,
    notify_ticket_after_commit,
    send_ticket_notification,
)


class FailingEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise SMTPException("SMTP unavailable")


@override_settings(DEFAULT_FROM_EMAIL="helpdesk@example.test")
class NotificationTests(TestCase):
    def setUp(self):
        self.payload = {
            "event": "created",
            "ticket_code": "HD-2026-001",
            "title": "Wi-Fi tại phòng A.201 không kết nối được",
            "to_email": "student@example.test",
            "ticket_url": "https://helpdesk.example.test/tickets/1/",
            "recipient_name": "Trường Lâm",
            "assignee_name": "Kỹ thuật viên A",
            "status_label": "Chờ tiếp nhận",
        }

    def test_all_events_have_plain_text_and_html(self):
        for event in ("created", "assigned", "resolved"):
            with self.subTest(event=event):
                message = build_ticket_email(**{**self.payload, "event": event})
                self.assertEqual(message.to, ["student@example.test"])
                self.assertEqual(message.from_email, "helpdesk@example.test")
                self.assertIn(self.payload["ticket_code"], message.subject)
                self.assertIn(self.payload["title"], message.body)
                self.assertIn(self.payload["ticket_url"], message.body)
                self.assertEqual(message.alternatives[0].mimetype, "text/html")
                self.assertIn('lang="vi"', message.alternatives[0].content)

    def test_delivery_has_exactly_the_intended_recipient_and_content(self):
        self.assertEqual(send_ticket_notification(**self.payload), 1)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["student@example.test"])
        self.assertEqual(message.cc, [])
        self.assertEqual(message.bcc, [])
        self.assertIn("Trường Lâm", message.body)
        self.assertIn("Chờ tiếp nhận", message.body)
        self.assertEqual(message.attachments, [])

    def test_html_escapes_user_supplied_names_and_title(self):
        message = build_ticket_email(**{
            **self.payload,
            "title": '<script>alert("x")</script>',
            "recipient_name": "<b>Student</b>",
            "assignee_name": "<img src=x onerror=alert(1)>",
        })
        html = message.alternatives[0].content
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;Student&lt;/b&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<img ", html)

    def test_subject_stays_on_one_line(self):
        message = build_ticket_email(**{
            **self.payload, "ticket_code": "HD-1\r\n", "title": "Mất mạng\r\nphòng A",
        })
        self.assertNotIn("\r", message.subject)
        self.assertNotIn("\n", message.subject)
        self.assertIn("Mất mạng phòng A", message.subject)
        self.assertEqual(message.message()["Bcc"], None)

    def test_invalid_payloads_are_rejected_before_delivery(self):
        invalid = (
            {"event": "unknown"}, {"ticket_code": ""}, {"title": "   "},
            {"to_email": ""}, {"to_email": "not-an-email"},
            {"to_email": "a@example.test\r\nBcc: other@example.test"},
            {"ticket_url": "javascript:alert(1)"}, {"ticket_url": "/tickets/1/"},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                with self.assertRaises(ValidationError):
                    send_ticket_notification(**{**self.payload, **changes})
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_optional_names_are_supported(self):
        payload = {key: value for key, value in self.payload.items()
                   if key not in ("recipient_name", "assignee_name", "status_label")}
        message = build_ticket_email(**payload)
        self.assertIn("Xin chào bạn", message.body)
        self.assertNotIn("None", message.body)

    @override_settings(MAILERS={"default": {"BACKEND": "notifications.tests.FailingEmailBackend"}})
    def test_direct_delivery_reports_backend_errors(self):
        with self.assertRaises(SMTPException):
            send_ticket_notification(**self.payload)

    def test_notification_waits_for_commit(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            notify_ticket_after_commit(**self.payload)
            self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_rollback_discards_the_notification(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            try:
                with transaction.atomic():
                    notify_ticket_after_commit(**self.payload)
                    raise RuntimeError("Ticket transaction rolled back")
            except RuntimeError:
                pass
        self.assertEqual(callbacks, [])
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(MAILERS={"default": {"BACKEND": "notifications.tests.FailingEmailBackend"}})
    def test_after_commit_failure_is_logged_and_later_callbacks_still_run(self):
        completed = []
        with self.assertLogs("django", level="ERROR"):
            with self.captureOnCommitCallbacks(execute=True):
                notify_ticket_after_commit(**self.payload)
                transaction.on_commit(lambda: completed.append(True))
        self.assertEqual(completed, [True])

    @override_settings(MAILERS={"default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {"host": "smtp.invalid", "timeout": 1},
    }})
    def test_preview_does_not_send_even_when_smtp_is_configured(self):
        output = StringIO()
        call_command("preview_ticket_email", "created", stdout=output)
        self.assertIn("HD-DEMO-001", output.getvalue())
        self.assertIn("demo@example.test", output.getvalue())
        self.assertIn("không gửi email", output.getvalue())
        self.assertEqual(len(mail.outbox), 0)

    def test_preview_can_write_utf8_html(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "assigned.html"
            call_command("preview_ticket_email", "assigned",
                         html_output=str(path), stdout=StringIO())
            content = path.read_text(encoding="utf-8")
        self.assertIn("Được phân công xử lý", content)
        self.assertIn("Kỹ thuật viên mẫu", content)
        self.assertIn('charset="utf-8"', content)
