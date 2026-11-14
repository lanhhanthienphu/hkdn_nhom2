import csv
import datetime
import io
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role

from .models import Attachment, Comment, Ticket, TicketHistory
from .reporting import report_time_series


@override_settings(TIME_ZONE='Asia/Ho_Chi_Minh', USE_TZ=True, FRONTEND_DEMO_ENABLED=None,
                   MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}})
class ReportFilterAndCsvTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(username='report-admin')
        cls.admin.profile.role = Role.objects.get(name='admin')
        cls.admin.profile.save()
        cls.superuser = User.objects.create_superuser(username='report-super', email='super@example.test')
        cls.tech = User.objects.create_user(username='report-tech', first_name='Trần', last_name='An')
        cls.tech.profile.role = Role.objects.get(name='technician')
        cls.tech.profile.save()
        cls.other_tech = User.objects.create_user(username='report-other-tech')
        cls.other_tech.profile.role = Role.objects.get(name='technician')
        cls.other_tech.profile.save()
        cls.owner = User.objects.create_user(username='report-owner', first_name='Lâm', last_name='Nguyễn')
        cls.staff_only = User.objects.create_user(username='report-staff', is_staff=True)
        cls.former_tech = User.objects.create_user(username='report-former', is_active=False)

        cls.first = cls.make_ticket('Đầu ngày', '2026-10-10T00:00:00', assigned_to=cls.tech)
        cls.last = cls.make_ticket('Cuối ngày', '2026-10-10T23:59:59.999999', assigned_to=cls.tech, status='resolved')
        cls.next_day = cls.make_ticket('Ngày kế tiếp', '2026-10-11T00:00:00', assigned_to=cls.other_tech, status='closed')
        cls.unassigned = cls.make_ticket('VPN chưa phân công', '2026-10-10T12:00:00', category='vpn', priority='normal', status='new')
        cls.printer = cls.make_ticket('Máy in', '2026-10-12T12:00:00', category='printer', assigned_to=cls.other_tech, priority='low')
        cls.former = cls.make_ticket('Lịch sử kỹ thuật viên cũ', '2026-10-10T12:00:00', assigned_to=cls.former_tech, status='closed', priority='urgent')
        cls.previous = cls.make_ticket('Trước khoảng chọn', '2026-10-09T23:59:59.999999', assigned_to=cls.tech)

    @classmethod
    def make_ticket(cls, title, local_date, **changes):
        ticket = Ticket.objects.create(**{
            'title': title, 'category': 'network', 'priority': 'high', 'status': 'in_progress',
            'location': 'A.201', 'description': 'Mô tả nội bộ không nằm trong CSV.', 'created_by': cls.owner,
            **changes,
        })
        instant = timezone.make_aware(datetime.datetime.fromisoformat(local_date))
        Ticket.objects.filter(pk=ticket.pk).update(created_at=instant)
        ticket.refresh_from_db()
        return ticket

    def setUp(self):
        self.client.force_login(self.admin)
        self.page_url = reverse('tickets:reports')
        self.csv_url = reverse('tickets:reports_export_csv')
        self.day_filter = {'date_from': '2026-10-10', 'date_to': '2026-10-10'}

    def download(self, params=None):
        response = self.client.get(self.csv_url, params or {})
        self.assertEqual(response.status_code, 200)
        try:
            content = b''.join(response.streaming_content)
        finally:
            response.close()
        return response, content, list(csv.reader(io.StringIO(content.decode('utf-8-sig'), newline='')))

    def ids(self, rows):
        return {int(row[0].removeprefix('HD-')) for row in rows[1:]}

    def test_same_local_day_includes_both_boundaries_and_excludes_adjacent_days(self):
        response = self.client.get(self.page_url, self.day_filter)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['total'], 4)
        _, _, rows = self.download(self.day_filter)
        self.assertEqual(self.ids(rows), {self.first.pk, self.last.pk, self.unassigned.pk, self.former.pk})
        self.assertIn('2026-10-10T00:00:00+07:00', str(rows))
        self.assertIn('2026-10-10T23:59:59+07:00', str(rows))

    def test_all_filters_apply_to_stats_charts_technicians_and_csv(self):
        params = {**self.day_filter, 'category': 'network', 'technician': self.tech.pk,
                  'status': 'resolved', 'priority': 'high'}
        response = self.client.get(self.page_url, params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['total'], 1)
        self.assertEqual(response.context['stats']['resolved'], 1)
        charts = response.context['chart_data']
        for name in ('status', 'priority', 'category'):
            self.assertEqual(sum(charts[name]['data']), 1)
        self.assertEqual(charts['status']['data'], [0, 0, 1, 0])
        for series in charts['time_series'].values():
            self.assertEqual(sum(series['data']), 1)
        self.assertEqual([(row['tech'].pk, row['total'], row['resolved']) for row in response.context['tech_stats']],
                         [(self.tech.pk, 1, 1)])
        _, _, rows = self.download(params)
        self.assertEqual(self.ids(rows), {self.last.pk})

    def test_open_ended_date_ranges_are_supported(self):
        _, _, rows = self.download({'date_to': '2026-10-09'})
        self.assertEqual(self.ids(rows), {self.previous.pk})
        _, _, rows = self.download({'date_from': '2026-10-11'})
        self.assertEqual(self.ids(rows), {self.next_day.pk, self.printer.pk})

    def test_unassigned_filter_matches_csv_and_has_no_technician_rows(self):
        response = self.client.get(self.page_url, {'technician': 'unassigned'})
        self.assertEqual(response.context['stats']['total'], 1)
        self.assertEqual(response.context['stats']['unassigned'], 1)
        self.assertEqual(response.context['tech_stats'], [])
        _, _, rows = self.download({'technician': 'unassigned'})
        self.assertEqual(self.ids(rows), {self.unassigned.pk})
        self.assertEqual(rows[1][7], 'Chưa phân công')

    def test_historical_inactive_assignee_remains_available(self):
        response = self.client.get(self.page_url, {'technician': self.former_tech.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['total'], 1)
        self.assertContains(response, 'đã vô hiệu hóa')
        _, _, rows = self.download({'technician': self.former_tech.pk})
        self.assertEqual(self.ids(rows), {self.former.pk})

    def test_empty_report_and_csv_header_only_are_valid(self):
        params = {'category': 'printer', 'technician': self.tech.pk}
        response = self.client.get(self.page_url, params)
        self.assertContains(response, 'Không có ticket phù hợp')
        self.assertEqual(response.context['stats']['total'], 0)
        self.assertEqual(sum(response.context['chart_data']['category']['data']), 0)
        _, content, rows = self.download(params)
        self.assertTrue(content.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 9)

    def test_no_filters_preserve_current_global_report(self):
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['stats']['total'], 7)
        _, _, rows = self.download()
        self.assertEqual(len(rows), 8)

    def test_invalid_filters_return_400_without_export_or_fallback_to_all_tickets(self):
        invalid = [
            {'date_from': 'not-a-date'}, {'date_to': '2026-02-30'},
            {'date_from': '2026-10-12', 'date_to': '2026-10-10'},
            {'category': 'not-a-category'}, {'status': 'fake'}, {'priority': 'fake'},
            {'technician': '-1'}, {'technician': str(2 ** 80)},
            {'technician': self.owner.pk}, {'date_from': '0001-01-01'},
        ]
        for params in invalid:
            for url in (self.page_url, self.csv_url):
                with self.subTest(params=params, url=url):
                    response = self.client.get(url, params)
                    self.assertEqual(response.status_code, 400)
                    self.assertTrue(response.context['report_form'].errors)
                    self.assertEqual(response.context['stats']['total'], 0)
                    self.assertFalse(response.has_header('Content-Disposition'))
                    self.assertNotContains(response, 'data-report-export', status_code=400)

    def test_invalid_filter_form_preserves_user_input(self):
        response = self.client.get(self.page_url, {'date_from': '2026-10-12', 'date_to': '2026-10-10'})
        self.assertContains(response, '2026-10-12', status_code=400)
        self.assertContains(response, '2026-10-10', status_code=400)
        self.assertContains(response, 'Từ ngày phải nhỏ hơn', status_code=400)

    def test_export_link_keeps_validated_filters_and_ignores_unknown_parameters(self):
        response = self.client.get(self.page_url, {**self.day_filter, 'category': 'network',
                                                  'q': '<script>alert(1)</script>', 'page': '2'})
        query = response.context['report_filter_query']
        self.assertIn('date_from=2026-10-10', query)
        self.assertIn('date_to=2026-10-10', query)
        self.assertIn('category=network', query)
        self.assertNotIn('page=', query)
        self.assertNotIn('q=', query)
        self.assertContains(response, self.csv_url + '?' + query.replace('&', '&amp;'))
        self.assertContains(response, f'href="{self.page_url}"')

    def test_anonymous_page_and_csv_require_login_and_keep_query_parameters(self):
        client = Client()
        for url in (self.page_url, self.csv_url):
            response = client.get(url, self.day_filter)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse('accounts:login') + '?next='))
            self.assertIn('date_from', response.url)
            self.assertFalse(response.has_header('Content-Disposition'))

    def test_ordinary_user_and_staff_without_role_cannot_view_or_export(self):
        for user in (self.owner, self.staff_only):
            self.client.force_login(user)
            for url in (self.page_url, self.csv_url):
                with self.subTest(user=user.username, url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 403)
                    self.assertFalse(response.has_header('Content-Disposition'))

    def test_admin_superuser_and_technician_keep_existing_global_report_permissions(self):
        for user in (self.admin, self.superuser, self.tech):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.client.get(self.page_url).context['stats']['total'], 7)
                _, _, rows = self.download()
                self.assertIn(self.other_tech.get_username(), str(rows))
                self.assertEqual(len(rows), 8)

    def test_csv_is_utf8_attachment_with_private_headers(self):
        response, content, rows = self.download()
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="helpdesk-tickets-'))
        self.assertTrue(response['Content-Disposition'].endswith('.csv"'))
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('private', response['Cache-Control'])
        self.assertIn('no-store', response['Cache-Control'])
        self.assertTrue(content.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(rows[0][0:2], ['Mã ticket', 'Tiêu đề'])
        self.assertIn('Lâm Nguyễn', str(rows))

    def test_csv_handles_vietnamese_quotes_commas_and_newlines_in_one_cell(self):
        title = 'Wi-Fi, phòng "A.201"\nMất kết nối'
        Ticket.objects.filter(pk=self.last.pk).update(title=title)
        _, _, rows = self.download({**self.day_filter, 'status': 'resolved'})
        self.assertEqual(rows[1][1], title)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[1]), 9)

    def test_csv_keeps_request_timezone_when_stream_is_consumed_later(self):
        with timezone.override('Asia/Ho_Chi_Minh'):
            response = self.client.get(self.csv_url, self.day_filter)
        try:
            with timezone.override('UTC'):
                rows = list(csv.reader(io.StringIO(b''.join(response.streaming_content).decode('utf-8-sig'))))
        finally:
            response.close()
        self.assertTrue(all(row[8].endswith('+07:00') for row in rows[1:]))

    def test_csv_formula_like_text_is_prefixed_inside_quoted_cells(self):
        formulas = ['=1+2', '+1+2', '-1+2', '@SUM(1,2)', '  =1+2', '\r\n=1+2',
                    '\t=1+2', '＝1+2', '＋1+2', '－1+2', '＠SUM(1,2)']
        for formula in formulas:
            with self.subTest(formula=formula):
                Ticket.objects.filter(pk=self.last.pk).update(title=formula)
                _, _, rows = self.download({**self.day_filter, 'status': 'resolved'})
                self.assertEqual(rows[1][1], '\t' + formula)
                self.assertEqual(len(rows[1]), 9)

    def test_csv_exports_all_matching_rows_beyond_any_page_size(self):
        Ticket.objects.bulk_create([
            Ticket(title=f'CSV bulk {i}', category='printer', priority='urgent', status='new',
                   location='B.201', description='Nội dung thử xuất nhiều ticket.', created_by=self.owner)
            for i in range(25)
        ])
        _, _, rows = self.download({'category': 'printer', 'priority': 'urgent', 'page': '2'})
        self.assertEqual(len(rows), 26)

    def test_csv_has_stable_order_for_equal_creation_times(self):
        Ticket.objects.filter(pk=self.last.pk).update(created_at=self.first.created_at)
        _, _, rows = self.download({**self.day_filter, 'technician': self.tech.pk})
        self.assertEqual([row[0] for row in rows[1:]], [self.last.code, self.first.code])

    def test_csv_does_not_read_attachments_or_export_private_file_data(self):
        Attachment.objects.create(ticket=self.first, file='tickets/private-path.log',
                                  original_name='private-name.log', size=42, uploaded_by=self.owner)
        with patch('tickets.attachment_storage.PrivateAttachmentStorage.open', side_effect=AssertionError('must not read files')):
            _, content, rows = self.download()
        self.assertEqual(len(rows[0]), 9)
        self.assertNotIn(b'private-path', content)
        self.assertNotIn(b'private-name', content)
        self.assertNotIn('Mô tả nội bộ', content.decode('utf-8-sig'))

    def test_report_and_export_are_read_only_and_do_not_send_email(self):
        models = (Ticket, TicketHistory, Comment, Attachment)
        before = [model.objects.count() for model in models]
        with self.captureOnCommitCallbacks(execute=True):
            self.client.get(self.page_url, self.day_filter)
            self.download(self.day_filter)
        self.assertEqual([model.objects.count() for model in models], before)
        self.assertEqual(mail.outbox, [])

    def test_report_routes_allow_head_and_reject_write_methods(self):
        for url in (self.page_url, self.csv_url):
            response = self.client.head(url)
            self.assertEqual(response.status_code, 200)
            response.close()
            for method in ('post', 'put', 'patch', 'delete'):
                with self.subTest(method=method, url=url):
                    self.assertEqual(getattr(self.client, method)(url).status_code, 405)

    def test_historic_time_series_uses_selected_end_day_and_filtered_set(self):
        response = self.client.get(self.page_url, self.day_filter)
        self.assertEqual(response.context['report_anchor'], datetime.date(2026, 10, 10))
        series = response.context['chart_data']['time_series']
        self.assertEqual(series['days_7']['labels'][-1], '10/10')
        self.assertEqual(series['months']['labels'][-1], '10/2026')
        for value in series.values():
            self.assertEqual(sum(value['data']), 4)

    def test_future_start_without_end_day_is_reflected_in_series(self):
        future = self.make_ticket('Ticket tương lai', '2100-01-07T12:00:00')
        response = self.client.get(self.page_url, {'date_from': '2100-01-07'})
        self.assertEqual(response.context['report_anchor'], datetime.date(2100, 1, 7))
        self.assertEqual(response.context['chart_data']['time_series']['days_7']['data'][-1], 1)
        _, _, rows = self.download({'date_from': '2100-01-07'})
        self.assertEqual(self.ids(rows), {future.pk})

    def test_leap_day_and_year_boundary_are_grouped_correctly(self):
        for day in ('2024-02-29', '2025-12-31'):
            with self.subTest(day=day):
                self.make_ticket('Ngày đặc biệt', day + 'T23:59:59')
                response = self.client.get(self.page_url, {'date_from': day, 'date_to': day})
                series = response.context['chart_data']['time_series']
                self.assertEqual(series['days_7']['data'][-1], 1)
                self.assertEqual(sum(series['months']['data']), 1)

    def test_time_series_does_not_issue_one_query_per_day_or_month(self):
        with CaptureQueriesContext(connection) as queries:
            series = report_time_series(Ticket.objects.all(), anchor=datetime.date(2026, 10, 12))
        self.assertLessEqual(len(queries), 3)
        self.assertEqual(sum(series['days_30']['data']), 7)
        self.assertEqual(sum(series['months']['data']), 7)

    def test_completion_count_includes_resolved_and_closed(self):
        response = self.client.get(self.page_url, {'status': 'closed'})
        self.assertEqual(response.context['stats']['total'], 2)
        self.assertEqual(response.context['stats']['completed'], 2)
        self.assertContains(response, '100%')
