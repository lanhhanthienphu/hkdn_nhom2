from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from notifications.ticket_events import notify_ticket_event

from .attachment_services import create_ticket_with_attachment
from .models import Attachment, Ticket, TicketHistory


LOC_MEMORY_MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}
FAIL_MAILERS = {'default': {'BACKEND': 'notifications.tests.FailingEmailBackend'}}
SITE = 'https://helpdesk.example.test'


class EmailFixture:
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user(username='email-owner', email='owner@example.test')
        cls.other = User.objects.create_user(username='email-other', email='other@example.test')
        cls.tech = User.objects.create_user(username='email-tech', email='tech@example.test')
        cls.tech.profile.role = Role.objects.get(name='technician')
        cls.tech.profile.save()
        cls.admin = User.objects.create_superuser(username='email-admin', email='admin@example.test')

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        setting = override_settings(PRIVATE_ATTACHMENT_ROOT=self.root)
        setting.enable()
        self.addCleanup(setting.disable)
        self.client.force_login(self.owner)
        self.data = {
            'title': 'Wi-Fi phòng A.201 mất kết nối', 'category': 'network',
            'priority': 'high', 'location': 'A.201',
            'description': 'Máy tính mất kết nối từ đầu giờ học, đã thử kết nối lại.',
        }

    def ticket(self, **changes):
        return Ticket.objects.create(**{**self.data, 'created_by': self.owner, **changes})

    def create(self, *, file=False):
        data = dict(self.data)
        if file:
            data['attachment'] = SimpleUploadedFile('network.log', b'private attachment bytes')
        return create_ticket_with_attachment(author=self.owner, data=data)


@override_settings(FRONTEND_DEMO_ENABLED=None, HELPDESK_BASE_URL=SITE, MAILERS=LOC_MEMORY_MAILERS)
class TicketEmailTests(EmailFixture, TestCase):
    def test_create_post_sends_owner_email_only_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(reverse('tickets:create'), {
                **self.data, 'to_email': 'attacker@example.test', 'created_by': self.other.pk,
                'ticket_url': 'https://attacker.example.test/',
                'attachment': SimpleUploadedFile('network.log', b'private attachment bytes'),
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(mail.outbox, [])
        ticket = Ticket.objects.get()
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [self.owner.email])
        self.assertIn('Đã tiếp nhận yêu cầu', message.subject)
        self.assertIn(SITE + reverse('tickets:detail', args=[ticket.pk]), message.body)
        self.assertNotIn('attacker', message.body)
        self.assertNotIn('private attachment bytes', message.body)
        self.assertEqual(message.attachments, [])
        self.assertEqual(ticket.attachments.count(), 1)

    def test_request_host_does_not_control_email_url(self):
        with override_settings(ALLOWED_HOSTS=['untrusted.example.test']):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(reverse('tickets:create'), self.data, HTTP_HOST='untrusted.example.test')
        self.assertEqual(response.status_code, 302)
        self.assertIn(SITE + '/tickets/', mail.outbox[0].body)
        self.assertNotIn('untrusted.example.test', mail.outbox[0].body)

    def test_assignment_post_emails_technician(self):
        ticket = self.ticket()
        self.client.force_login(self.tech)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('tickets:assign', args=[ticket.pk]), {
                'technician_id': self.tech.pk,
            })
            self.assertEqual(mail.outbox, [])
        self.assertEqual(response.status_code, 302)
        self.assertEqual([message.to for message in mail.outbox], [[self.tech.email]])
        self.assertIn('Được phân công xử lý', mail.outbox[0].subject)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')
        self.assertEqual(ticket.histories.get().changed_by, self.tech)

    def test_resolution_post_emails_requester(self):
        ticket = self.ticket(status='in_progress', assigned_to=self.tech)
        self.client.force_login(self.tech)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('tickets:change_status', args=[ticket.pk]), {'status': 'resolved'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual([message.to for message in mail.outbox], [[self.owner.email]])
        self.assertIn('đã được giải quyết', mail.outbox[0].subject)

    def test_repeated_assignment_uses_database_state_even_with_stale_instance(self):
        ticket = self.ticket()
        stale = Ticket.objects.get(pk=ticket.pk)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(ticket.assign_technician(self.tech, by=self.tech))
            self.assertFalse(stale.assign_technician(self.tech, by=self.tech))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ticket.histories.count(), 1)
        self.assertEqual(stale.assigned_to_id, self.tech.pk)
        self.assertEqual(stale.status, 'in_progress')

    def test_repeated_resolution_uses_database_state_even_with_stale_instance(self):
        ticket = self.ticket(status='in_progress')
        stale = Ticket.objects.get(pk=ticket.pk)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(ticket.change_status('resolved', by=self.tech))
            self.assertFalse(stale.change_status('resolved', by=self.tech))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ticket.histories.count(), 1)
        self.assertEqual(stale.status, 'resolved')

    def test_reassignment_emails_only_new_assignee(self):
        ticket = self.ticket(assigned_to=self.tech, status='in_progress')
        with self.captureOnCommitCallbacks(execute=True):
            ticket.assign_technician(self.admin, by=self.admin)
        self.assertEqual([message.to for message in mail.outbox], [[self.admin.email]])

    def test_reopened_then_resolved_is_a_new_event(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            ticket.change_status('resolved', by=self.tech)
            ticket.change_status('in_progress', by=self.tech)
            ticket.change_status('resolved', by=self.tech)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(ticket.histories.count(), 3)

    def test_other_status_changes_and_plain_save_do_not_send_email(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            ticket.change_status('in_progress', by=self.tech)
            ticket.change_status('closed', by=self.tech)
            ticket.title = 'Đổi tiêu đề ticket'
            ticket.save(update_fields=['title'])
        self.assertEqual(mail.outbox, [])

    def test_invalid_status_in_model_does_not_mutate_or_notify(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(ValidationError):
                ticket.change_status('not-a-status', by=self.tech)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'new')
        self.assertFalse(ticket.histories.exists())
        self.assertEqual(mail.outbox, [])

    def test_unprivileged_requests_cannot_trigger_lifecycle_email(self):
        ticket = self.ticket()
        self.client.force_login(self.other)
        with self.captureOnCommitCallbacks(execute=True):
            assigned = self.client.post(reverse('tickets:assign', args=[ticket.pk]), {'technician_id': self.tech.pk})
            resolved = self.client.post(reverse('tickets:change_status', args=[ticket.pk]), {'status': 'resolved'})
        self.assertEqual(assigned.status_code, 403)
        self.assertEqual(resolved.status_code, 403)
        self.assertEqual(mail.outbox, [])
        self.assertFalse(ticket.histories.exists())

    def test_anonymous_post_does_not_create_or_notify(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = Client().post(reverse('tickets:create'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Ticket.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_invalid_or_inactive_assignment_target_is_rejected(self):
        ticket = self.ticket()
        self.tech.is_active = False
        self.tech.save(update_fields=['is_active'])
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            for target in (self.other, self.tech):
                with self.subTest(target=target.username):
                    response = self.client.post(reverse('tickets:assign', args=[ticket.pk]), {
                        'technician_id': target.pk,
                    }, follow=True)
                    self.assertContains(response, 'Chỉ được phân công cho kỹ thuật viên')
        ticket.refresh_from_db()
        self.assertIsNone(ticket.assigned_to_id)
        self.assertEqual(ticket.status, 'new')
        self.assertFalse(ticket.histories.exists())
        self.assertEqual(mail.outbox, [])

    def test_invalid_assignment_id_returns_404(self):
        ticket = self.ticket()
        self.client.force_login(self.tech)
        with self.captureOnCommitCallbacks(execute=True):
            for value in ('', 'bad', '-1', str(2 ** 70), '99999'):
                with self.subTest(value=value):
                    response = self.client.post(reverse('tickets:assign', args=[ticket.pk]), {'technician_id': value})
                    self.assertEqual(response.status_code, 404)
        self.assertEqual(mail.outbox, [])

    def test_blank_email_skips_notification_without_losing_ticket(self):
        self.owner.email = ''
        self.owner.save(update_fields=['email'])
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            ticket = self.create()
        self.assertEqual(callbacks, [])
        self.assertTrue(Ticket.objects.filter(pk=ticket.pk).exists())

    def test_invalid_email_is_logged_but_ticket_and_file_are_saved(self):
        self.owner.email = 'invalid-address'
        self.owner.save(update_fields=['email'])
        with self.assertLogs('notifications.ticket_events', level='WARNING'):
            with self.captureOnCommitCallbacks(execute=True):
                ticket = self.create(file=True)
        self.assertEqual(mail.outbox, [])
        self.assertEqual(ticket.attachments.count(), 1)
        self.assertEqual(len(list(self.root.rglob('*.log'))), 1)

    def test_inactive_requester_does_not_receive_resolution_email(self):
        ticket = self.ticket()
        self.owner.is_active = False
        self.owner.save(update_fields=['is_active'])
        with self.captureOnCommitCallbacks(execute=True):
            ticket.change_status('resolved', by=self.tech)
        self.assertEqual(ticket.status, 'resolved')
        self.assertEqual(mail.outbox, [])

    def test_invalid_origin_is_logged_but_does_not_break_creation(self):
        for origin in ('', '/tickets/', 'javascript:alert(1)', 'https://user:pass@example.test',
                       SITE + '?next=evil', SITE + '/extra', SITE + '#fragment', SITE + '?', SITE + '#'):
            with self.subTest(origin=origin), override_settings(HELPDESK_BASE_URL=origin):
                with self.assertLogs('notifications.ticket_events', level='WARNING'):
                    with self.captureOnCommitCallbacks(execute=True):
                        ticket = self.create()
                self.assertTrue(Ticket.objects.filter(pk=ticket.pk).exists())
        self.assertEqual(mail.outbox, [])

    def test_local_origin_and_trailing_slash_work(self):
        with override_settings(HELPDESK_BASE_URL='http://127.0.0.1:8000/'):
            with self.captureOnCommitCallbacks(execute=True):
                ticket = self.create()
        self.assertIn(f'http://127.0.0.1:8000/tickets/{ticket.pk}/', mail.outbox[0].body)

    def test_creation_failure_rolls_back_ticket_file_and_email(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with patch('tickets.attachment_services.TicketHistory.objects.create', side_effect=DatabaseError('unavailable')):
                with self.assertRaises(DatabaseError):
                    self.create(file=True)
        self.assertEqual(callbacks, [])
        self.assertFalse(Ticket.objects.exists())
        self.assertFalse(Attachment.objects.exists())
        self.assertEqual(list(self.root.rglob('*.log')), [])
        self.assertEqual(mail.outbox, [])

    def test_history_failure_rolls_back_assignment_and_resolution(self):
        ticket = self.ticket()
        for operation in (
            lambda: ticket.assign_technician(self.tech, by=self.tech),
            lambda: ticket.change_status('resolved', by=self.tech),
        ):
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with patch.object(TicketHistory, 'save', side_effect=DatabaseError('history unavailable')):
                    with self.assertRaises(DatabaseError):
                        operation()
            ticket.refresh_from_db()
            self.assertIsNone(ticket.assigned_to_id)
            self.assertEqual(ticket.status, 'new')
            self.assertEqual(callbacks, [])
        self.assertEqual(mail.outbox, [])

    def test_outer_rollback_discards_assignment_and_resolution_emails(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    ticket.assign_technician(self.tech, by=self.tech)
                    ticket.change_status('resolved', by=self.tech)
                    raise RuntimeError('cancel workflow')
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'new')
        self.assertIsNone(ticket.assigned_to_id)
        self.assertFalse(ticket.histories.exists())
        self.assertEqual(callbacks, [])
        self.assertEqual(mail.outbox, [])

    @override_settings(FRONTEND_DEMO_ENABLED=True)
    def test_demo_create_does_not_send_real_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('tickets:create'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Ticket.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_reply_does_not_send_another_lifecycle_email(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse('tickets:detail', args=[ticket.pk]), {'content': 'Bổ sung thông tin sự cố.'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ticket.comments.count(), 1)
        self.assertEqual(mail.outbox, [])

    def test_adapter_rejects_unsaved_ticket_and_unknown_event(self):
        with self.assertRaises(ValueError):
            notify_ticket_event(Ticket(**self.data, created_by=self.owner), 'created')
        with self.assertRaises(ValueError):
            notify_ticket_event(self.ticket(), 'unknown')


@override_settings(FRONTEND_DEMO_ENABLED=None, HELPDESK_BASE_URL=SITE, MAILERS=LOC_MEMORY_MAILERS)
class TicketAdminEmailTests(EmailFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def admin_post(self, ticket=None, **changes):
        url = reverse('admin:tickets_ticket_change', args=[ticket.pk]) if ticket else reverse('admin:tickets_ticket_add')
        page = self.client.get(url)
        self.assertEqual(page.status_code, 200)
        form = page.context['adminform'].form
        data = {field.html_name: field.value() if field.value() is not None else '' for field in form}
        if ticket is None:
            data.update(self.data, created_by=self.owner.pk)
        for inline in page.context['inline_admin_formsets']:
            for field in inline.formset.management_form:
                data[field.html_name] = field.value()
            for inline_form in inline.formset.forms:
                for field in inline_form:
                    data[field.html_name] = field.value() if field.value() is not None else ''
        data.update(changes)
        data['_save'] = 'Save'
        return self.client.post(url, data)

    def test_admin_creation_sends_created_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post()
            self.assertEqual(mail.outbox, [])
        self.assertEqual(response.status_code, 302)
        self.assertEqual([message.to for message in mail.outbox], [[self.owner.email]])
        self.assertEqual(TicketHistory.objects.count(), 1)

    def test_admin_creation_with_assignee_sends_created_and_assigned(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(assigned_to=self.tech.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual([message.to for message in mail.outbox], [[self.owner.email], [self.tech.email]])
        self.assertEqual(Ticket.objects.get().status, 'in_progress')

    def test_admin_failure_rolls_back_edit_and_notification(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with patch.object(TicketHistory, 'save', side_effect=DatabaseError('history unavailable')):
                with self.assertRaises(DatabaseError):
                    self.admin_post(ticket, status='resolved')
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'new')
        self.assertEqual(callbacks, [])
        self.assertEqual(mail.outbox, [])

    def test_admin_assignment_resolution_and_repeated_save(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(ticket, assigned_to=self.tech.pk)
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')
        self.assertEqual([message.to for message in mail.outbox], [[self.tech.email]])
        self.assertEqual(ticket.histories.count(), 1)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(ticket, status='resolved')
        self.assertEqual(response.status_code, 302)
        self.assertEqual([message.to for message in mail.outbox], [[self.tech.email], [self.owner.email]])
        self.assertEqual(ticket.histories.count(), 2)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(ticket)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(ticket.histories.count(), 2)

    def test_admin_metadata_change_does_not_notify(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(ticket, title='Cập nhật tên sự cố Wi-Fi')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mail.outbox, [])
        self.assertFalse(ticket.histories.exists())

    def test_admin_rejects_non_technician_assignment(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(ticket, assigned_to=self.other.pk)
        self.assertEqual(response.status_code, 200)
        self.assertIn('assigned_to', response.context['adminform'].form.errors)
        ticket.refresh_from_db()
        self.assertIsNone(ticket.assigned_to_id)
        self.assertEqual(mail.outbox, [])

    def test_admin_unassignment_has_history_but_no_email(self):
        ticket = self.ticket(status='in_progress', assigned_to=self.tech)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(ticket, assigned_to='')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ticket.histories.count(), 1)
        self.assertEqual(mail.outbox, [])

    def test_admin_simultaneous_assignment_and_resolution_sends_both_events(self):
        ticket = self.ticket()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.admin_post(ticket, assigned_to=self.tech.pk, status='resolved')
        self.assertEqual(response.status_code, 302)
        self.assertEqual([message.to for message in mail.outbox], [[self.tech.email], [self.owner.email]])
        self.assertEqual(ticket.histories.count(), 2)


@override_settings(FRONTEND_DEMO_ENABLED=None, HELPDESK_BASE_URL=SITE, MAILERS=FAIL_MAILERS)
class TicketEmailCommitFailureTests(TransactionTestCase):
    def test_smtp_failure_after_real_commit_keeps_ticket_file_and_later_callbacks(self):
        owner = get_user_model().objects.create_user(username='commit-owner', email='owner@example.test')
        with TemporaryDirectory() as directory, override_settings(PRIVATE_ATTACHMENT_ROOT=directory):
            with self.assertLogs('django', level='ERROR'):
                ticket = create_ticket_with_attachment(author=owner, data={
                    'title': 'Mạng Wi-Fi không kết nối', 'category': 'network',
                    'priority': 'normal', 'location': 'A.201', 'description': 'Mất mạng từ đầu giờ học.',
                    'attachment': SimpleUploadedFile('network.log', b'keep file after SMTP failure'),
                })
            self.assertTrue(Ticket.objects.filter(pk=ticket.pk).exists())
            self.assertEqual(ticket.histories.count(), 1)
            attachment = ticket.attachments.get()
            self.assertTrue(attachment.file.storage.exists(attachment.file.name))

            completed = []
            with self.assertLogs('django', level='ERROR'):
                with transaction.atomic():
                    ticket.change_status('resolved', by=owner)
                    transaction.on_commit(lambda: completed.append(True))
            ticket.refresh_from_db()
            self.assertEqual(ticket.status, 'resolved')
            self.assertEqual(completed, [True])
            self.assertTrue(attachment.file.storage.exists(attachment.file.name))
