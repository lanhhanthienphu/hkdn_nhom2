from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import Role

from .attachment_services import create_ticket_with_attachment
from .attachment_storage import PrivateAttachmentStorage
from .attachment_validators import MAX_ATTACHMENT_BYTES
from .models import Attachment, Ticket, TicketHistory


@override_settings(FRONTEND_DEMO_ENABLED=None)
class TicketAttachmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user(username='file-owner')
        cls.other = User.objects.create_user(username='file-other')
        cls.assignee = User.objects.create_user(username='file-assignee')
        cls.technician = User.objects.create_user(username='file-technician')
        cls.technician.profile.role = Role.objects.get(name='technician')
        cls.technician.profile.save()
        cls.admin = User.objects.create_user(username='file-admin')
        cls.admin.profile.role = Role.objects.get(name='admin')
        cls.admin.profile.save()
        cls.superuser = User.objects.create_user(username='file-superuser', is_superuser=True, is_staff=True)
        cls.staff_only = User.objects.create_user(username='file-staff', is_staff=True)

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        setting = override_settings(PRIVATE_ATTACHMENT_ROOT=self.root)
        setting.enable()
        self.addCleanup(setting.disable)
        self.client.force_login(self.owner)
        self.data = {
            'title': 'Wi-Fi phòng A.201 mất kết nối',
            'category': 'network', 'priority': 'high', 'location': 'A.201',
            'description': 'Máy tính mất kết nối từ đầu giờ học, đã thử kết nối lại.',
        }

    def upload(self, name='network.LOG', content=b'connection timed out\n'):
        return SimpleUploadedFile(name, content, content_type='text/plain')

    def create(self, *, upload=None, author=None):
        return create_ticket_with_attachment(
            author=author or self.owner,
            data={**self.data, 'attachment': upload if upload is not None else self.upload()},
        )

    def url(self, attachment, *, ticket_id=None):
        return reverse('tickets:attachment_download', args=[
            ticket_id if ticket_id is not None else attachment.ticket_id, attachment.pk,
        ])

    def files(self):
        return [path for path in self.root.rglob('*') if path.is_file()]

    def downloaded_bytes(self, response):
        try:
            return b''.join(response.streaming_content)
        finally:
            response.close()

    def test_create_upload_and_download_after_a_new_login(self):
        content = 'Mất kết nối lúc 08:30 tại A.201.\n'.encode()
        response = self.client.post(reverse('tickets:create'), {
            **self.data, 'attachment': self.upload('nhật ký mạng.LOG', content),
        })
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get()
        attachment = Attachment.objects.get(ticket=ticket)
        self.assertEqual(ticket.created_by, self.owner)
        self.assertEqual(attachment.uploaded_by, self.owner)
        self.assertEqual(attachment.original_name, 'nhật ký mạng.LOG')
        self.assertEqual(attachment.size, len(content))
        self.assertEqual(ticket.attachment_name, attachment.original_name)
        self.assertEqual(ticket.attachment_size, len(content))
        self.assertEqual(TicketHistory.objects.filter(ticket=ticket).count(), 1)
        self.assertEqual(len(self.files()), 1)
        self.assertEqual(self.files()[0].read_bytes(), content)

        self.client.logout()
        another_session = Client()
        another_session.force_login(self.owner)
        self.assertContains(another_session.get(response.url), self.url(attachment))
        downloaded = another_session.get(self.url(attachment))
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(self.downloaded_bytes(downloaded), content)

    def test_ticket_without_file_still_saves(self):
        response = self.client.post(reverse('tickets:create'), self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(TicketHistory.objects.count(), 1)
        self.assertFalse(Attachment.objects.exists())
        self.assertEqual(self.files(), [])

    def test_binary_image_is_preserved_even_when_upload_cursor_has_moved(self):
        buffer = BytesIO()
        Image.new('RGB', (2, 2), color='blue').save(buffer, format='PNG')
        content = buffer.getvalue()
        upload = self.upload('screen.PNG', content)
        upload.seek(8)
        attachment = self.create(upload=upload).attachments.get()
        response = self.client.get(self.url(attachment))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.downloaded_bytes(response), content)

    def test_invalid_files_do_not_create_tickets_or_physical_files(self):
        for name, content in (
            ('script.exe', b'not allowed'), ('fake.png', b'not an image'),
            ('empty.txt', b''), ('huge.log', b'x' * (MAX_ATTACHMENT_BYTES + 1)),
        ):
            with self.subTest(name=name):
                response = self.client.post(reverse('tickets:create'), {
                    **self.data, 'attachment': self.upload(name, content),
                })
                self.assertEqual(response.status_code, 200)
                self.assertIn('attachment', response.context['form'].errors)
                self.assertFalse(Ticket.objects.exists())
                self.assertFalse(Attachment.objects.exists())
                self.assertEqual(self.files(), [])

    def test_invalid_ticket_form_does_not_save_an_otherwise_valid_file(self):
        response = self.client.post(reverse('tickets:create'), {
            **self.data, 'title': 'bad', 'attachment': self.upload(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)
        self.assertFalse(Ticket.objects.exists())
        self.assertEqual(self.files(), [])

    def test_service_also_rejects_invalid_file_bytes(self):
        with self.assertRaises(ValidationError):
            self.create(upload=self.upload('fake.pdf', b'not a pdf'))
        self.assertFalse(Ticket.objects.exists())
        self.assertEqual(self.files(), [])

    def test_same_filenames_do_not_overwrite_existing_content(self):
        first = self.create(upload=self.upload('same.log', b'first log')).attachments.get()
        second = self.create(upload=self.upload('same.log', b'second log')).attachments.get()
        self.assertNotEqual(first.file.name, second.file.name)
        self.assertEqual(self.downloaded_bytes(self.client.get(self.url(first))), b'first log')
        self.assertEqual(self.downloaded_bytes(self.client.get(self.url(second))), b'second log')
        self.assertEqual(len(self.files()), 2)

    def test_storage_name_does_not_include_client_path_or_original_filename(self):
        attachment = self.create(upload=self.upload(r'C:\fakepath\network.LOG')).attachments.get()
        self.assertEqual(attachment.original_name, 'network.LOG')
        self.assertNotIn('fakepath', attachment.file.name)
        self.assertNotIn('network', attachment.file.name)
        self.assertNotIn('\\', attachment.file.name)
        self.assertTrue(attachment.file.name.endswith('.log'))
        self.assertTrue(self.files()[0].resolve().is_relative_to(self.root.resolve()))

    def test_stored_size_is_actual_byte_size(self):
        upload = self.upload(content=b'actual bytes in file')
        upload.size = 1
        attachment = self.create(upload=upload).attachments.get()
        self.assertEqual(attachment.size, len(b'actual bytes in file'))

    def test_download_permissions_match_ticket_visibility(self):
        ticket = self.create()
        ticket.assigned_to = self.assignee
        ticket.save(update_fields=['assigned_to'])
        attachment = ticket.attachments.get()
        for user in (self.owner, self.assignee, self.technician, self.admin, self.superuser):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(self.url(attachment))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.downloaded_bytes(response), b'connection timed out\n')

    def test_unrelated_users_cannot_download_even_if_staff(self):
        attachment = self.create().attachments.get()
        for user in (self.other, self.staff_only):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                with patch.object(PrivateAttachmentStorage, 'open') as opened:
                    response = self.client.get(self.url(attachment))
                self.assertEqual(response.status_code, 404)
                opened.assert_not_called()

    def test_anonymous_download_requires_login(self):
        attachment = self.create().attachments.get()
        with patch.object(PrivateAttachmentStorage, 'open') as opened:
            response = Client().get(self.url(attachment))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('accounts:login') + '?next='))
        opened.assert_not_called()

    def test_download_id_must_belong_to_the_ticket_in_the_url(self):
        attachment = self.create().attachments.get()
        another = self.create()
        self.assertEqual(self.client.get(self.url(attachment, ticket_id=another.pk)).status_code, 404)
        missing = reverse('tickets:attachment_download', args=[attachment.ticket_id, attachment.pk + 9999])
        self.assertEqual(self.client.get(missing).status_code, 404)

    def test_missing_physical_file_returns_404(self):
        attachment = self.create().attachments.get()
        attachment.file.storage.delete(attachment.file.name)
        self.assertEqual(self.client.get(self.url(attachment)).status_code, 404)

    def test_download_headers_force_private_attachment_and_preserve_unicode_name(self):
        attachment = self.create(upload=self.upload('nhật ký.LOG')).attachments.get()
        response = self.client.get(self.url(attachment))
        try:
            self.assertEqual(response['Content-Type'], 'application/octet-stream')
            self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
            self.assertIn("filename*=utf-8''", response['Content-Disposition'])
            self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
            self.assertIn('private', response['Cache-Control'])
            self.assertIn('no-store', response['Cache-Control'])
        finally:
            response.close()

    def test_download_accepts_head_but_rejects_post(self):
        attachment = self.create().attachments.get()
        response = self.client.head(self.url(attachment))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response['Content-Length']), attachment.size)
        self.assertEqual(self.downloaded_bytes(response), b'')
        self.assertEqual(self.client.post(self.url(attachment)).status_code, 405)

    def test_files_have_no_public_url_or_public_media_route(self):
        attachment = self.create().attachments.get()
        with self.assertRaises(ValueError):
            _ = attachment.file.url
        for prefix in ('/media/', '/private_uploads/'):
            self.assertEqual(self.client.get(prefix + attachment.file.name).status_code, 404)

    def test_detail_escapes_original_name_and_shows_download_link(self):
        attachment = self.create(upload=self.upload('network<probe>.log')).attachments.get()
        response = self.client.get(reverse('tickets:detail', args=[attachment.ticket_id]))
        self.assertContains(response, 'network&lt;probe&gt;.log')
        self.assertNotContains(response, '<probe>')
        self.assertContains(response, self.url(attachment))
        self.assertNotContains(response, 'chưa có nội dung để tải')
        self.assertNotContains(response, 'Thêm phản hồi xem thử')

    def test_legacy_metadata_does_not_create_fake_downloads(self):
        ticket = Ticket.objects.create(
            **self.data, created_by=self.owner, attachment_name='old.log', attachment_size=20,
        )
        response = self.client.get(reverse('tickets:detail', args=[ticket.pk]))
        self.assertContains(response, 'old.log')
        self.assertContains(response, 'chưa có nội dung để tải')
        self.assertNotContains(response, '/attachments/')
        self.assertFalse(Attachment.objects.exists())

    def test_create_page_describes_real_uploads(self):
        response = self.client.get(reverse('tickets:create'))
        self.assertContains(response, 'multipart/form-data')
        self.assertNotContains(response, 'Tạo ticket xem thử')
        self.assertNotContains(response, 'chưa lưu nội dung file')

    def test_database_failure_after_file_save_rolls_back_and_removes_file(self):
        with patch('tickets.attachment_services.TicketHistory.objects.create', side_effect=DatabaseError('offline')):
            with self.assertRaises(DatabaseError):
                self.create()
        self.assertFalse(Ticket.objects.exists())
        self.assertFalse(Attachment.objects.exists())
        self.assertFalse(TicketHistory.objects.exists())
        self.assertEqual(self.files(), [])

    def test_error_after_storage_write_rolls_back_and_removes_file(self):
        with patch.object(PrivateAttachmentStorage, 'size', side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):
                self.create()
        self.assertFalse(Ticket.objects.exists())
        self.assertFalse(Attachment.objects.exists())
        self.assertEqual(self.files(), [])

    def test_storage_failure_keeps_form_values_and_does_not_report_success(self):
        with patch.object(PrivateAttachmentStorage, 'save', side_effect=OSError('disk full')):
            with self.assertLogs('tickets.views', level='ERROR'):
                response = self.client.post(reverse('tickets:create'), {**self.data, 'attachment': self.upload()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Chưa lưu được ticket')
        self.assertEqual(response.context['form']['title'].value(), self.data['title'])
        self.assertFalse(Ticket.objects.exists())
        self.assertFalse(Attachment.objects.exists())
        self.assertEqual(self.files(), [])

    def test_file_is_removed_only_after_ticket_deletion_commits(self):
        ticket = self.create()
        path = self.files()[0]
        with self.captureOnCommitCallbacks(execute=True):
            ticket.delete()
            self.assertTrue(path.exists())
            self.assertFalse(Attachment.objects.exists())
        self.assertFalse(path.exists())

    def test_rolled_back_deletion_keeps_the_file_and_database_rows(self):
        ticket = self.create()
        ticket_id = ticket.pk
        path = self.files()[0]
        with self.captureOnCommitCallbacks(execute=True):
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    ticket.delete()
                    raise RuntimeError('cancel delete')
        self.assertTrue(Ticket.objects.filter(pk=ticket_id).exists())
        self.assertTrue(Attachment.objects.filter(ticket_id=ticket_id).exists())
        self.assertTrue(path.exists())

    def test_unexpected_outer_transaction_is_rejected_before_writing_file(self):
        with transaction.atomic():
            with self.assertRaises(RuntimeError):
                self.create()
        self.assertFalse(Ticket.objects.exists())
        self.assertEqual(self.files(), [])

    def test_anonymous_upload_does_not_write_anything(self):
        response = Client().post(reverse('tickets:create'), {**self.data, 'attachment': self.upload()})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Ticket.objects.exists())
        self.assertEqual(self.files(), [])

    def test_csrf_required_for_upload_even_after_login(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        response = client.post(reverse('tickets:create'), {**self.data, 'attachment': self.upload()})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Ticket.objects.exists())
        self.assertEqual(self.files(), [])

    @override_settings(FRONTEND_DEMO_ENABLED=True)
    def test_demo_upload_remains_metadata_only(self):
        response = self.client.post(reverse('tickets:create'), {**self.data, 'attachment': self.upload()})
        self.assertEqual(response.status_code, 302)
        detail = self.client.get(response.url)
        self.assertContains(detail, 'chưa có nội dung để tải')
        self.assertContains(detail, 'Thêm phản hồi xem thử')
        self.assertFalse(Ticket.objects.exists())
        self.assertFalse(Attachment.objects.exists())
        self.assertEqual(self.files(), [])

    def test_admin_shows_download_link_without_accessing_public_file_url(self):
        ticket = self.create()
        attachment = ticket.attachments.get()
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('admin:tickets_ticket_change', args=[ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.url(attachment))
