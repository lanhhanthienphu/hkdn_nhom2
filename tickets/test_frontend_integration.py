"""End-user acceptance tests for the Django frontend and the real backend."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role

from .models import Attachment, Comment, Ticket


@override_settings(
    FRONTEND_DEMO_ENABLED=None,
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}},
)
class FrontendDatabaseIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user(
            username='frontend-owner', password='TestPassword_2026!',
            first_name='Minh', last_name='Khôi',
        )
        cls.other = User.objects.create_user(username='frontend-other')
        cls.technician = User.objects.create_user(
            username='frontend-technician', first_name='Trần Minh', last_name='Hoàng',
        )
        cls.technician.profile.role = Role.objects.get(name='technician')
        cls.technician.profile.save()

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        setting = override_settings(PRIVATE_ATTACHMENT_ROOT=Path(directory.name))
        setting.enable()
        self.addCleanup(setting.disable)
        self.client.force_login(self.owner)
        self.data = {
            'title': 'Wi-Fi phòng A.201 không kết nối được',
            'category': 'network', 'priority': 'high', 'location': 'A.201',
            'description': 'Mất kết nối từ đầu giờ học, đã thử kết nối lại nhiều lần.',
        }

    def ticket(self, **changes):
        return Ticket.objects.create(**{**self.data, 'created_by': self.owner, **changes})

    def test_customer_flow_persists_and_displays_backend_updates(self):
        content = 'Wi-Fi A.201 mất kết nối lúc 08:30.\n'.encode()
        response = self.client.post(reverse('tickets:create'), {
            **self.data,
            'created_by': self.other.pk,
            'attachment': SimpleUploadedFile('wifi.log', content, content_type='text/plain'),
        })
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get()
        self.assertEqual(ticket.created_by, self.owner)
        attachment = Attachment.objects.get(ticket=ticket)
        detail_url = reverse('tickets:detail', args=[ticket.pk])
        download_url = reverse('tickets:attachment_download', args=[ticket.pk, attachment.pk])

        # A new authenticated session must still see the saved ticket and bytes.
        self.client.logout()
        self.assertTrue(self.client.login(username=self.owner.username, password='TestPassword_2026!'))
        home = self.client.get(reverse('tickets:home'))
        self.assertEqual(home.context['stats']['total'], 1)
        self.assertContains(home, ticket.title)
        self.assertContains(self.client.get(detail_url), download_url)
        download = self.client.get(download_url)
        self.assertEqual(download.status_code, 200)
        try:
            self.assertEqual(b''.join(download.streaming_content), content)
        finally:
            download.close()

        # Exercise the existing backend routes; the customer page must reflect them.
        technician = Client()
        technician.force_login(self.technician)
        assigned = technician.post(reverse('tickets:assign', args=[ticket.pk]), {
            'technician_id': self.technician.pk, 'note': 'Đã nhận xử lý mạng A.201',
        })
        self.assertEqual(assigned.status_code, 302)
        detail = self.client.get(detail_url)
        self.assertContains(detail, self.technician.get_full_name())
        self.assertContains(detail, 'Đã nhận xử lý mạng A.201')
        self.assertEqual(detail.context['ticket'].status, 'in_progress')

        public_reply = 'Em đã khởi động lại máy nhưng vẫn chưa vào mạng được.'
        self.assertEqual(self.client.post(detail_url, {'content': public_reply}).status_code, 302)
        technical_reply = 'Đã kiểm tra và thay cổng switch cho phòng A.201.'
        self.assertEqual(technician.post(detail_url, {'content': technical_reply}).status_code, 302)
        for _ in range(2):
            detail = self.client.get(detail_url)
            self.assertContains(detail, public_reply)
            self.assertContains(detail, technical_reply)
        self.assertEqual(Comment.objects.filter(ticket=ticket).count(), 2)

        for status in ['resolved', 'closed']:
            changed = technician.post(reverse('tickets:change_status', args=[ticket.pk]), {'status': status})
            self.assertEqual(changed.status_code, 302)
            self.assertEqual(self.client.get(detail_url).context['ticket'].status, status)
        closed = self.client.post(detail_url, {'content': 'Không được ghi thêm khi đã đóng.'})
        self.assertContains(closed, 'Ticket đã đóng')
        self.assertEqual(Comment.objects.filter(ticket=ticket).count(), 2)

        # Search, dashboard, detail, comments and downloads all enforce isolation.
        other = Client()
        other.force_login(self.other)
        self.assertEqual(other.get(reverse('tickets:home')).context['stats']['total'], 0)
        self.assertEqual(other.get(reverse('tickets:list'), {'q': ticket.code}).context['page_obj'].paginator.count, 0)
        self.assertEqual(other.get(detail_url).status_code, 404)
        self.assertEqual(other.post(detail_url, {'content': 'Không được gửi phản hồi này.'}).status_code, 404)
        self.assertEqual(other.get(download_url).status_code, 404)

    def test_search_finds_the_reporters_displayed_full_name(self):
        ticket = self.ticket()
        response = self.client.get(reverse('tickets:list'), {'q': self.owner.get_full_name()})
        self.assertEqual(list(response.context['page_obj']), [ticket])

    def test_unusual_numeric_searches_do_not_break_the_page(self):
        self.ticket()
        for query in ['²', 'HD-²', '9' * 150, 'HD-' + '9' * 147]:
            with self.subTest(query=query):
                response = self.client.get(reverse('tickets:list'), {'q': query})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['page_obj'].paginator.count, 0)

    def test_filter_pagination_has_stable_order_for_equal_dates(self):
        tickets = [self.ticket(title=f'Wi-Fi phòng A.201 lần {i}', status='in_progress') for i in range(7)]
        self.ticket(title='Wi-Fi khác độ ưu tiên', priority='low', status='in_progress')
        self.ticket(created_by=self.other, status='in_progress')
        Ticket.objects.update(created_at=timezone.now())
        ids = [ticket.pk for ticket in tickets]
        filters = {'q': 'Wi-Fi', 'status': 'in_progress', 'category': 'network', 'priority': 'high'}
        for sort in ['newest', 'oldest', 'priority']:
            with self.subTest(sort=sort):
                actual = []
                for page in [1, 2]:
                    response = self.client.get(reverse('tickets:list'), {**filters, 'sort': sort, 'page': page})
                    self.assertEqual(response.context['page_obj'].paginator.count, 7)
                    actual.extend(ticket.pk for ticket in response.context['page_obj'])
                self.assertEqual(actual, sorted(ids, reverse=sort != 'oldest'))

    def test_reply_save_failure_preserves_the_entered_content(self):
        ticket = self.ticket()
        reply = 'Em đã thử khởi động lại máy nhưng vẫn còn lỗi.'
        with self.assertLogs('tickets.views', level='ERROR'):
            with patch('tickets.views.Comment.objects.create', side_effect=OperationalError('test failure')):
                response = self.client.post(reverse('tickets:detail', args=[ticket.pk]), {'content': reply})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertContains(response, reply)
        self.assertFalse(Comment.objects.filter(ticket=ticket).exists())

    def test_detail_shows_saved_assignee_even_before_status_changes(self):
        ticket = self.ticket(assigned_to=self.technician, status='new')
        response = self.client.get(reverse('tickets:detail', args=[ticket.pk]))
        self.assertContains(response, self.technician.get_full_name())
