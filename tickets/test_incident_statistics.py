import csv
import io

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import Role

from .models import Ticket, TicketHistory
from .views import get_category_chart_data, get_category_stats, get_network_incident_types_stats


@override_settings(FRONTEND_DEMO_ENABLED=None)
class IncidentCategoryStatisticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user(username='category-owner')
        cls.other = User.objects.create_user(username='category-other')
        cls.admin = User.objects.create_user(username='category-admin')
        cls.admin.profile.role = Role.objects.get(name='admin')
        cls.admin.profile.save()

    def setUp(self):
        self.client.force_login(self.admin)
        self.labels = [label for _, label in Ticket.CATEGORY_CHOICES]

    def ticket(self, category='network', **changes):
        return Ticket.objects.create(**{
            'title': 'Kiểm tra thống kê sự cố', 'category': category, 'priority': 'normal',
            'status': 'new', 'location': 'A.201', 'description': 'Mô tả chi tiết sự cố tại phòng A.201.',
            'created_by': self.owner, **changes,
        })

    def csv_rows(self, params=None):
        response = self.client.get(reverse('tickets:reports_export_csv'), params or {})
        self.assertEqual(response.status_code, 200)
        try:
            return list(csv.reader(io.StringIO(b''.join(response.streaming_content).decode('utf-8-sig'))))
        finally:
            response.close()

    def test_each_stored_category_has_one_separate_bucket(self):
        for category, _ in Ticket.CATEGORY_CHOICES:
            self.ticket(category)
        labels, data = get_category_stats()
        self.assertEqual(labels, self.labels)
        self.assertEqual(data, [1, 1, 1, 1])
        self.assertEqual(sum(data), Ticket.objects.count())

    def test_multiple_network_keywords_in_one_ticket_do_not_inflate_total(self):
        self.ticket(title='Internet Wi-Fi LAN router switch server access point',
                    description='Internet lỗi Wi-Fi, cáp RJ45 và máy chủ cũng cần kiểm tra.')
        labels, data = get_network_incident_types_stats()
        self.assertEqual(labels, self.labels)
        self.assertEqual(data, [1, 0, 0, 0])
        self.assertEqual(sum(data), 1)

    def test_saved_vpn_printer_and_other_groups_are_not_overridden_by_words(self):
        for category in ('vpn', 'printer', 'other'):
            self.ticket(category, title='Internet Wi-Fi LAN router server', description='VPN, máy in và access point.')
        _, data = get_category_stats()
        self.assertEqual(data, [0, 1, 1, 1])

    def test_laptop_text_does_not_match_access_point_substring(self):
        self.ticket('other', title='Laptop bị lỗi màn hình')
        self.ticket('printer', title='Laptop không in được qua Wi-Fi')
        _, data = get_category_stats()
        self.assertEqual(data, [0, 0, 1, 1])

    def test_supplied_queryset_scope_is_preserved_including_an_empty_scope(self):
        self.ticket('network')
        self.ticket('printer', created_by=self.other)
        labels, data = get_category_stats(Ticket.objects.filter(created_by=self.owner))
        self.assertEqual(labels, self.labels)
        self.assertEqual(data, [1, 0, 0, 0])
        self.assertEqual(get_category_stats(Ticket.objects.none()), (self.labels, [0, 0, 0, 0]))

    def test_blank_and_unknown_legacy_values_share_a_visible_unclassified_bucket(self):
        original = ['', 'legacy-server', 'VPN', '   ']
        ids = [self.ticket(category).pk for category in original]
        self.ticket('other')
        labels, data = get_category_stats()
        self.assertEqual(labels, self.labels + ['Chưa xác định'])
        self.assertEqual(data, [0, 0, 0, 1, 4])
        self.assertEqual(list(Ticket.objects.filter(pk__in=ids).order_by('pk').values_list('category', flat=True)), original)

    def test_legacy_raw_values_are_not_used_as_chart_labels(self):
        self.ticket('<script>alert(1)</script>')
        labels, data = get_category_stats()
        self.assertNotIn('<script>alert(1)</script>', labels)
        self.assertEqual(labels[-1], 'Chưa xác định')
        self.assertEqual(sum(data), 1)

    def test_empty_database_keeps_four_zero_groups_without_a_fallback_group(self):
        chart = get_category_chart_data()
        self.assertEqual(chart['labels'], self.labels)
        self.assertEqual(chart['data'], [0, 0, 0, 0])
        self.assertFalse(chart['has_unclassified'])

    def test_duplicate_history_join_rows_count_one_ticket_once(self):
        ticket = self.ticket('vpn')
        for _ in range(3):
            TicketHistory.objects.create(ticket=ticket, changed_by=self.admin, old_status='new', new_status='new')
        queryset = Ticket.objects.filter(histories__isnull=False)
        self.assertEqual(queryset.count(), 3)
        _, data = get_category_stats(queryset)
        self.assertEqual(data, [0, 1, 0, 0])

    def test_group_order_and_colors_stay_stable_across_query_ordering(self):
        self.ticket('other')
        self.ticket('vpn')
        self.ticket('network')
        first = get_category_chart_data(Ticket.objects.order_by('category'))
        second = get_category_chart_data(Ticket.objects.order_by('-pk'))
        self.assertEqual(first, second)
        self.assertEqual(first['labels'], self.labels)

    def test_dashboard_chart_total_matches_ticket_total_with_legacy_data(self):
        for category in ('network', 'vpn', 'printer', 'other', 'legacy', ''):
            self.ticket(category, title='Internet Wi-Fi router máy chủ')
        response = self.client.get(reverse('tickets:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        chart = response.context['chart_data']['category']
        self.assertEqual(sum(chart['data']), response.context['stats']['total'])
        self.assertEqual(sum(chart['data']), 6)
        self.assertEqual(len(chart['colors']), len(chart['labels']))
        self.assertContains(response, 'Thống kê theo nhóm sự cố')
        self.assertContains(response, 'cần kiểm tra lại dữ liệu')

    def test_filtered_report_category_total_matches_csv_and_selected_group(self):
        chosen = self.ticket('printer', status='resolved', priority='high', title='Máy in Wi-Fi router')
        self.ticket('printer', status='new', priority='high')
        self.ticket('network', status='resolved', priority='high')
        params = {'category': 'printer', 'status': 'resolved', 'priority': 'high'}
        response = self.client.get(reverse('tickets:reports'), params)
        chart = response.context['chart_data']['category']
        rows = self.csv_rows(params)
        self.assertEqual(chart['data'], [0, 0, 1, 0])
        self.assertEqual(sum(chart['data']), response.context['stats']['total'])
        self.assertEqual(len(rows) - 1, sum(chart['data']))
        self.assertEqual(rows[1][0], chosen.code)
        self.assertEqual(len(rows[0]), 11)

    def test_unfiltered_dashboard_and_report_use_same_category_data_and_palette(self):
        for category in ('network', 'printer', 'legacy'):
            self.ticket(category)
        admin = self.client.get(reverse('tickets:admin_dashboard'))
        report = self.client.get(reverse('tickets:reports'))
        self.assertEqual(admin.context['chart_data']['category'], report.context['chart_data']['category'])
        self.assertEqual(sum(report.context['chart_data']['category']['data']), 3)

    def test_unclassified_notice_is_hidden_for_valid_groups(self):
        self.ticket('network')
        for name in ('admin_dashboard', 'reports'):
            with self.subTest(page=name):
                response = self.client.get(reverse('tickets:' + name))
                self.assertFalse(response.context['chart_data']['category']['has_unclassified'])
                self.assertNotContains(response, 'có ticket mang nhóm trống')

    def test_grouping_is_one_database_query_even_with_many_tickets(self):
        Ticket.objects.bulk_create([
            Ticket(title=f'Internet Wi-Fi router {index}', category='network', created_by=self.owner,
                   location='A.201', description='Mô tả sự cố mạng.') for index in range(50)
        ])
        with CaptureQueriesContext(connection) as queries:
            _, data = get_category_stats()
        self.assertEqual(sum(data), 50)
        self.assertEqual(len(queries), 1)

    def test_correcting_the_stored_group_moves_ticket_without_duplicating_it(self):
        ticket = self.ticket('network', title='Internet Wi-Fi router máy in')
        self.assertEqual(get_category_stats()[1], [1, 0, 0, 0])
        Ticket.objects.filter(pk=ticket.pk).update(category='printer')
        self.assertEqual(get_category_stats()[1], [0, 0, 1, 0])
        self.assertEqual(sum(get_category_stats()[1]), 1)
