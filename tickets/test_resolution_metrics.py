import csv
import datetime
import io
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role

from .models import Ticket, TicketHistory
from .resolution_metrics import (
    first_resolution_row, first_resolution_summary, format_resolution_duration,
    resolution_minutes, with_first_resolution,
)


@override_settings(TIME_ZONE='UTC', USE_TZ=True, FRONTEND_DEMO_ENABLED=None,
                   MAILERS={'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}})
class FirstResolutionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user(username='time-owner', email='owner@example.test')
        cls.admin = User.objects.create_user(username='time-admin')
        cls.admin.profile.role = Role.objects.get(name='admin')
        cls.admin.profile.save()
        cls.tech = User.objects.create_user(username='time-tech', email='tech@example.test')
        cls.tech.profile.role = Role.objects.get(name='technician')
        cls.tech.profile.save()

    def setUp(self):
        self.start = datetime.datetime(2026, 11, 16, 1, tzinfo=datetime.timezone.utc)
        self.client.force_login(self.admin)
        self.page_url = reverse('tickets:reports')
        self.csv_url = reverse('tickets:reports_export_csv')

    def ticket(self, **changes):
        ticket = Ticket.objects.create(**{
            'title': 'Kiểm tra thời gian giải quyết', 'category': 'network', 'priority': 'normal',
            'location': 'A.201', 'description': 'Không kết nối được mạng tại phòng A.201.',
            'status': 'resolved', 'created_by': self.owner, 'assigned_to': self.tech, **changes,
        })
        Ticket.objects.filter(pk=ticket.pk).update(created_at=self.start)
        ticket.refresh_from_db()
        return ticket

    def history(self, ticket, old='in_progress', new='resolved', *, minutes=20, at=None):
        history = TicketHistory.objects.create(ticket=ticket, changed_by=self.tech,
                                              old_status=old, new_status=new, assigned_to=self.tech)
        instant = at if at is not None else self.start + datetime.timedelta(minutes=minutes)
        TicketHistory.objects.filter(pk=history.pk).update(created_at=instant)
        history.refresh_from_db()
        return history

    def measured(self, ticket):
        return with_first_resolution(Ticket.objects.filter(pk=ticket.pk)).get()

    def summary(self):
        return first_resolution_summary(with_first_resolution(Ticket.objects.all()))

    def csv_rows(self, params=None):
        response = self.client.get(self.csv_url, params or {})
        self.assertEqual(response.status_code, 200)
        try:
            return list(csv.reader(io.StringIO(b''.join(response.streaming_content).decode('utf-8-sig'))))
        finally:
            response.close()

    def test_first_valid_resolution_is_used_once_even_with_multiple_resolutions(self):
        ticket = self.ticket()
        self.history(ticket, minutes=20)
        self.history(ticket, 'resolved', 'in_progress', minutes=25)
        self.history(ticket, minutes=60)
        result = self.measured(ticket)
        self.assertEqual(result.first_resolved_at, self.start + datetime.timedelta(minutes=20))
        self.assertEqual(result.first_resolution_duration, datetime.timedelta(minutes=20))
        self.assertEqual(self.summary()['measured'], 1)

    def test_reopened_ticket_keeps_first_resolution_and_remains_in_average(self):
        ticket = self.ticket(status='in_progress')
        self.history(ticket, minutes=20)
        self.history(ticket, 'resolved', 'in_progress', minutes=25)
        result = self.measured(ticket)
        self.assertEqual(result.first_resolution_state, 'measured')
        self.assertEqual(self.summary()['average'], datetime.timedelta(minutes=20))
        self.assertEqual(self.summary()['pending'], 0)

    def test_closed_ticket_uses_resolution_time_instead_of_close_time(self):
        ticket = self.ticket(status='closed')
        self.history(ticket, minutes=20)
        self.history(ticket, 'resolved', 'closed', minutes=90)
        self.assertEqual(self.measured(ticket).first_resolution_duration, datetime.timedelta(minutes=20))

    def test_assignment_after_resolution_does_not_change_first_resolution(self):
        ticket = self.ticket()
        self.history(ticket, minutes=20)
        self.history(ticket, 'resolved', 'resolved', minutes=55)
        self.assertEqual(self.measured(ticket).first_resolution_duration, datetime.timedelta(minutes=20))

    def test_assignment_or_creation_in_resolved_state_is_not_a_resolution_transition(self):
        for old in ('resolved', ''):
            with self.subTest(old=old):
                ticket = self.ticket()
                self.history(ticket, old=old)
                result = self.measured(ticket)
                self.assertIsNone(result.first_resolved_at)
                self.assertIsNone(result.first_resolution_duration)
                self.assertEqual(result.first_resolution_state, 'missing')
        self.assertIsNone(self.summary()['average'])

    def test_earlier_evidence_of_resolution_blocks_claiming_a_later_event_as_first(self):
        for old, new in [('resolved', 'resolved'), ('resolved', 'in_progress'), ('', 'resolved')]:
            with self.subTest(old=old, new=new):
                ticket = self.ticket()
                self.history(ticket, old=old, new=new, minutes=10)
                self.history(ticket, minutes=60)
                result = self.measured(ticket)
                self.assertIsNone(result.first_resolved_at)
                self.assertEqual(result.first_resolution_state, 'missing')

    def test_resolution_before_creation_is_missing_data_even_if_later_event_is_valid(self):
        ticket = self.ticket()
        self.history(ticket, minutes=-5)
        self.history(ticket, minutes=20)
        result = self.measured(ticket)
        self.assertEqual(result.first_resolution_state, 'missing')
        self.assertIsNone(result.first_resolution_duration)
        self.assertIsNone(self.summary()['average'])

    def test_new_and_in_progress_without_resolution_are_pending(self):
        for status in ('new', 'in_progress'):
            ticket = self.ticket(status=status)
            self.assertEqual(self.measured(ticket).first_resolution_state, 'pending')
        summary = self.summary()
        self.assertEqual((summary['pending'], summary['missing'], summary['measured']), (2, 0, 0))

    def test_resolved_and_closed_without_history_are_missing(self):
        for status in ('resolved', 'closed'):
            ticket = self.ticket(status=status)
            self.assertEqual(self.measured(ticket).first_resolution_state, 'missing')
        self.assertEqual(self.summary()['missing'], 2)
        self.assertEqual(self.summary()['average_label'], 'Chưa có dữ liệu')

    def test_unrecognized_previous_status_does_not_create_a_fake_measurement(self):
        ticket = self.ticket()
        self.history(ticket, old='unknown')
        self.assertEqual(self.measured(ticket).first_resolution_state, 'missing')

    def test_first_recorded_resolution_can_be_a_transition_from_closed(self):
        ticket = self.ticket()
        self.history(ticket, 'new', 'closed', minutes=5)
        self.history(ticket, 'closed', 'resolved', minutes=20)
        self.assertEqual(self.measured(ticket).first_resolution_duration, datetime.timedelta(minutes=20))

    def test_actual_zero_duration_is_measured_and_included_in_average(self):
        ticket = self.ticket()
        self.history(ticket, minutes=0)
        another = self.ticket()
        self.history(another, minutes=20)
        result = self.measured(ticket)
        self.assertEqual(result.first_resolution_duration, datetime.timedelta(0))
        self.assertEqual(first_resolution_row(result)['duration_label'], '0 giây')
        self.assertEqual(resolution_minutes(result.first_resolution_duration), '0.00')
        self.assertEqual(self.summary()['measured'], 2)
        self.assertEqual(self.summary()['average'], datetime.timedelta(minutes=10))

    def test_missing_pending_and_duplicate_history_rows_do_not_bias_average(self):
        first, second = self.ticket(), self.ticket()
        self.history(first, minutes=20)
        self.history(first, 'resolved', 'resolved', minutes=30)
        self.history(second, minutes=40)
        self.ticket(status='new')
        self.ticket(status='resolved')
        summary = self.summary()
        self.assertEqual((summary['total'], summary['measured'], summary['pending'], summary['missing']), (4, 2, 1, 1))
        self.assertEqual(summary['average'], datetime.timedelta(minutes=30))
        self.assertEqual(summary['average_label'], '30 phút')

    def test_report_and_csv_share_all_filters_and_resolution_cohort(self):
        selected = self.ticket(category='vpn', priority='high')
        self.history(selected, minutes=20)
        excluded = self.ticket(category='network')
        self.history(excluded, minutes=80)
        params = {'date_from': '2026-11-16', 'date_to': '2026-11-16', 'category': 'vpn',
                  'technician': self.tech.pk, 'status': 'resolved', 'priority': 'high'}
        page = self.client.get(self.page_url, params)
        self.assertEqual(page.context['resolution_stats']['average'], datetime.timedelta(minutes=20))
        self.assertEqual([row['ticket'].pk for row in page.context['resolution_rows']], [selected.pk])
        rows = self.csv_rows(params)
        self.assertEqual(rows[1][0], selected.code)
        self.assertEqual(Decimal(rows[1][10]), Decimal('20.00'))
        self.assertEqual(len(rows), 2)

    def test_resolution_page_uses_ten_rows_but_average_includes_whole_filtered_set(self):
        tickets = []
        for minutes in range(1, 12):
            ticket = self.ticket()
            self.history(ticket, minutes=minutes)
            tickets.append(ticket)
        first = self.client.get(self.page_url, {'category': 'network'})
        second = self.client.get(self.page_url, {'category': 'network', 'resolution_page': '2'})
        self.assertEqual(first.context['resolution_stats']['average'], datetime.timedelta(minutes=6))
        self.assertEqual(second.context['resolution_stats']['average'], datetime.timedelta(minutes=6))
        self.assertEqual(len(first.context['resolution_rows']), 10)
        self.assertEqual(len(second.context['resolution_rows']), 1)
        self.assertContains(first, 'category=network&amp;resolution_page=2#resolution-times')
        actual = [row['ticket'].pk for response in (first, second) for row in response.context['resolution_rows']]
        self.assertEqual(actual, [ticket.pk for ticket in reversed(tickets)])

    def test_invalid_resolution_page_does_not_break_report(self):
        self.ticket()
        for page in ('bad', '0', '-1', '9' * 100):
            with self.subTest(page=page):
                response = self.client.get(self.page_url, {'resolution_page': page})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.context['resolution_rows']), 1)

    def test_csv_appends_two_columns_without_changing_existing_column_positions(self):
        ticket = self.ticket()
        self.history(ticket, minutes=20)
        rows = self.csv_rows()
        self.assertEqual(len(rows[0]), 11)
        self.assertEqual(rows[0][8], 'Ngày tạo (ISO 8601)')
        self.assertEqual(rows[0][9], 'Ngày giải quyết lần đầu (ISO 8601)')
        self.assertEqual(rows[0][10], 'Thời gian giải quyết lần đầu (phút)')
        self.assertEqual(rows[1][9], (self.start + datetime.timedelta(minutes=20)).isoformat(timespec='seconds'))
        self.assertEqual(rows[1][10], '20.00')

    def test_csv_unknown_times_are_blank_while_valid_zero_is_numeric(self):
        pending, missing, zero = self.ticket(status='new'), self.ticket(), self.ticket()
        self.history(zero, minutes=0)
        rows = {row[0]: row for row in self.csv_rows()[1:]}
        self.assertEqual(rows[pending.code][9:], ['', ''])
        self.assertEqual(rows[missing.code][9:], ['', ''])
        self.assertEqual(rows[zero.code][10], '0.00')

    def test_csv_exports_all_rows_even_if_report_table_is_on_second_page(self):
        for _ in range(12):
            self.history(self.ticket())
        rows = self.csv_rows({'resolution_page': '2'})
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(row[10] == '20.00' for row in rows[1:]))

    def test_updating_metadata_does_not_change_resolution_measurement(self):
        ticket = self.ticket()
        self.history(ticket, minutes=20)
        ticket.title = 'Tiêu đề mới sau khi xử lý'
        ticket.save()
        self.assertEqual(self.measured(ticket).first_resolution_duration, datetime.timedelta(minutes=20))

    def test_resolution_rows_and_summary_do_not_query_each_ticket_history_separately(self):
        for _ in range(20):
            self.history(self.ticket())
        queryset = with_first_resolution(Ticket.objects.select_related('created_by', 'assigned_to'))
        with CaptureQueriesContext(connection) as queries:
            rows = [first_resolution_row(ticket) for ticket in queryset]
            summary = first_resolution_summary(queryset)
        self.assertEqual(len(rows), 20)
        self.assertEqual(summary['average'], datetime.timedelta(minutes=20))
        self.assertLessEqual(len(queries), 2)

    def test_real_create_assign_resolve_flow_measures_creation_to_resolution_including_wait(self):
        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            with patch('django.utils.timezone.now', return_value=self.start):
                response = self.client.post(reverse('tickets:create'), {
                    'title': 'Wi-Fi mất kết nối cần hỗ trợ', 'category': 'network', 'priority': 'high',
                    'location': 'A.201', 'description': 'Mất kết nối từ đầu giờ học, đã thử kết nối lại.',
                })
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get()
        self.client.force_login(self.tech)
        with self.captureOnCommitCallbacks(execute=True):
            with patch('django.utils.timezone.now', return_value=self.start + datetime.timedelta(minutes=5)):
                self.assertEqual(self.client.post(reverse('tickets:assign', args=[ticket.pk]),
                                                 {'technician_id': self.tech.pk}).status_code, 302)
            with patch('django.utils.timezone.now', return_value=self.start + datetime.timedelta(minutes=20)):
                self.assertEqual(self.client.post(reverse('tickets:change_status', args=[ticket.pk]),
                                                 {'status': 'resolved'}).status_code, 302)
        self.assertEqual(len(mail.outbox), 3)
        before_histories = TicketHistory.objects.count()
        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(self.page_url)
            self.assertEqual(response.context['resolution_stats']['average'], datetime.timedelta(minutes=20))
            self.assertEqual(self.csv_rows()[1][10], '20.00')
        self.assertEqual(TicketHistory.objects.count(), before_histories)
        self.assertEqual(len(mail.outbox), 3)

    def test_new_resolution_table_escapes_ticket_title(self):
        self.history(self.ticket(title='<script>alert(1)</script>'))
        response = self.client.get(self.page_url)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_date_filters_still_use_creation_date_not_resolution_date(self):
        ticket = self.ticket()
        self.history(ticket, at=self.start + datetime.timedelta(days=2))
        created_day = self.client.get(self.page_url, {'date_from': '2026-11-16', 'date_to': '2026-11-16'})
        resolved_day = self.client.get(self.page_url, {'date_from': '2026-11-18', 'date_to': '2026-11-18'})
        self.assertEqual(created_day.context['resolution_stats']['measured'], 1)
        self.assertEqual(created_day.context['resolution_stats']['average'], datetime.timedelta(days=2))
        self.assertEqual(resolved_day.context['resolution_stats']['measured'], 0)

    def test_rounding_preserves_measurement_state_and_uses_explicit_units(self):
        ticket = self.ticket()
        delta = datetime.timedelta(microseconds=600000)
        self.history(ticket, at=self.start + delta)
        self.assertEqual(self.measured(ticket).first_resolution_state, 'measured')
        self.assertEqual(self.summary()['average_label'], '1 giây')
        self.assertEqual(self.csv_rows()[1][10], '0.01')
        long_duration = datetime.timedelta(days=1, hours=2, minutes=3, seconds=4)
        self.assertEqual(format_resolution_duration(long_duration), '1 ngày 2 giờ 3 phút 4 giây')

    @override_settings(TIME_ZONE='Asia/Ho_Chi_Minh')
    def test_export_and_table_use_configured_timezone_for_resolution_timestamp(self):
        ticket = self.ticket()
        self.history(ticket, minutes=20)
        response = self.client.get(self.page_url)
        self.assertContains(response, '08:20:00, 16/11/2026')
        self.assertEqual(self.csv_rows()[1][9], '2026-11-16T08:20:00+07:00')

    def test_deleted_history_is_not_reconstructed_from_updated_at(self):
        ticket = self.ticket()
        history = self.history(ticket)
        self.assertEqual(self.summary()['measured'], 1)
        history.delete()
        self.assertEqual(self.summary()['measured'], 0)
        self.assertEqual(self.summary()['missing'], 1)
        self.assertIsNone(self.summary()['average'])
