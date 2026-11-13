import datetime
import json
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role, UserProfile
from tickets.models import Comment, Ticket, TicketHistory

User = get_user_model()


class DashboardAndManagementTests(TestCase):
    def setUp(self):
        # 1. Tạo các vai trò
        self.role_admin = Role.objects.get_or_create(name='admin', defaults={'description': 'Quản trị viên'})[0]
        self.role_tech = Role.objects.get_or_create(name='technician', defaults={'description': 'Kỹ thuật viên'})[0]
        self.role_user = Role.objects.get_or_create(name='user', defaults={'description': 'Người dùng'})[0]

        # 2. Tạo users
        self.admin_user = User.objects.create_user(username='admin_boss', password='Password123!', email='admin@helpdesk.vn')
        self.admin_user.profile.role = self.role_admin
        self.admin_user.profile.save()

        self.tech_user_1 = User.objects.create_user(username='tech_tuan', password='Password123!', email='tuan@helpdesk.vn')
        self.tech_user_1.profile.role = self.role_tech
        self.tech_user_1.profile.department = 'Đội Hạ Tầng Mạng'
        self.tech_user_1.profile.save()

        self.tech_user_2 = User.objects.create_user(username='tech_dung', password='Password123!', email='dung@helpdesk.vn')
        self.tech_user_2.profile.role = self.role_tech
        self.tech_user_2.profile.department = 'Hỗ Trợ Máy Trạm'
        self.tech_user_2.profile.save()

        self.regular_user = User.objects.create_user(username='staff_lan', password='Password123!', email='lan@helpdesk.vn')
        self.regular_user.profile.role = self.role_user
        self.regular_user.profile.save()

        # 3. Tạo một số Ticket thực tế
        self.ticket_1 = Ticket.objects.create(
            title='Mất kết nối Switch phòng Lab 3',
            category='network',
            priority='urgent',
            location='Phòng Lab 3',
            description='Switch Cisco 2960 báo đèn cam và rớt toàn bộ mạng nội bộ.',
            created_by=self.regular_user,
            status='new',
        )

        self.ticket_2 = Ticket.objects.create(
            title='Lỗi VPN từ xa của phòng Kế toán',
            category='vpn',
            priority='high',
            location='Tầng 2 Block A',
            description='Không thể quay số VPN qua FortiClient.',
            created_by=self.regular_user,
            assigned_to=self.tech_user_1,
            status='in_progress',
        )

        self.ticket_3 = Ticket.objects.create(
            title='Kẹt giấy máy in phòng Giám đốc',
            category='printer',
            priority='normal',
            location='Phòng GĐ',
            description='Máy in HP LaserJet kẹt giấy liên tục.',
            created_by=self.regular_user,
            assigned_to=self.tech_user_2,
            status='resolved',
        )

        self.ticket_4 = Ticket.objects.create(
            title='Cáp mạng đứt tại bàn làm việc',
            category='other',
            priority='low',
            location='Bàn 12 Tầng 4',
            description='Đầu bấm mạng RJ45 bị gãy lẫy nhựa.',
            created_by=self.regular_user,
            assigned_to=self.tech_user_1,
            status='closed',
        )

    # --- Test Dashboard Dispatcher ---
    def test_dashboard_dispatcher_routing(self):
        client = Client()

        # Admin -> admin_dashboard
        client.force_login(self.admin_user)
        resp = client.get(reverse('tickets:dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('tickets:admin_dashboard'))

        # Tech -> technician_dashboard
        client.force_login(self.tech_user_1)
        resp = client.get(reverse('tickets:dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('tickets:technician_dashboard'))

        # User -> tickets:home
        client.force_login(self.regular_user)
        resp = client.get(reverse('tickets:dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('tickets:home'))

    # --- Test Admin Dashboard ---
    def test_admin_dashboard_permissions(self):
        client = Client()

        # Regular user bị chặn 403
        client.force_login(self.regular_user)
        resp = client.get(reverse('tickets:admin_dashboard'))
        self.assertEqual(resp.status_code, 403)

        # Tech không phải admin bị chặn 403
        client.force_login(self.tech_user_1)
        resp = client.get(reverse('tickets:admin_dashboard'))
        self.assertEqual(resp.status_code, 403)

        # Admin truy cập thành công 200
        client.force_login(self.admin_user)
        resp = client.get(reverse('tickets:admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Dashboard Quản Trị Hệ Thống')

    def test_admin_dashboard_statistics_and_charts(self):
        client = Client()
        client.force_login(self.admin_user)
        resp = client.get(reverse('tickets:admin_dashboard'))

        self.assertEqual(resp.status_code, 200)
        stats = resp.context['stats']
        self.assertEqual(stats['total'], 4)
        self.assertEqual(stats['open'], 1)
        self.assertEqual(stats['in_progress'], 1)
        self.assertEqual(stats['resolved'], 1)
        self.assertEqual(stats['closed'], 1)

        priority_stats = resp.context['priority_stats']
        self.assertEqual(priority_stats['urgent'], 1)
        self.assertEqual(priority_stats['high'], 1)
        self.assertEqual(priority_stats['normal'], 1)
        self.assertEqual(priority_stats['low'], 1)

        # Kiểm tra Chart.js JSON data
        chart_data = resp.context['chart_data']
        self.assertIn('status', chart_data)
        self.assertIn('priority', chart_data)
        self.assertIn('category', chart_data)
        self.assertIn('time_series', chart_data)

    def test_admin_dashboard_filters(self):
        client = Client()
        client.force_login(self.admin_user)

        # Lọc theo trạng thái
        resp = client.get(reverse('tickets:admin_dashboard') + '?status=new')
        items = list(resp.context['page_obj'])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0], self.ticket_1)

        # Lọc theo KTV phụ trách
        resp_tech = client.get(reverse('tickets:admin_dashboard') + f'?technician={self.tech_user_1.id}')
        items_tech = list(resp_tech.context['page_obj'])
        self.assertEqual(len(items_tech), 2)
        self.assertIn(self.ticket_2, items_tech)
        self.assertIn(self.ticket_4, items_tech)

        # Tìm kiếm theo từ khóa
        resp_search = client.get(reverse('tickets:admin_dashboard') + '?q=Switch')
        items_search = list(resp_search.context['page_obj'])
        self.assertEqual(len(items_search), 1)
        self.assertEqual(items_search[0], self.ticket_1)

    # --- Test Technician Dashboard ---
    def test_technician_dashboard_permissions_and_isolation(self):
        client = Client()

        # Regular user bị chặn 403
        client.force_login(self.regular_user)
        resp = client.get(reverse('tickets:technician_dashboard'))
        self.assertEqual(resp.status_code, 403)

        # Tech 1 chỉ nhìn thấy ticket của Tech 1
        client.force_login(self.tech_user_1)
        resp = client.get(reverse('tickets:technician_dashboard'))
        self.assertEqual(resp.status_code, 200)

        tech_tickets = list(resp.context['page_obj'])
        self.assertEqual(len(tech_tickets), 2)
        self.assertIn(self.ticket_2, tech_tickets)
        self.assertIn(self.ticket_4, tech_tickets)
        self.assertNotIn(self.ticket_1, tech_tickets)
        self.assertNotIn(self.ticket_3, tech_tickets)

        # Kiểm tra stats của Tech 1
        stats = resp.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['in_progress'], 1)
        self.assertEqual(stats['closed'], 1)

    def test_technician_cannot_reassign_to_other_technician(self):
        client = Client()
        client.force_login(self.tech_user_1)

        # Tech 1 cố tình gán ticket 2 cho Tech 2 -> Phải bị chặn 403!
        resp = client.post(reverse('tickets:assign', args=[self.ticket_2.id]), {
            'technician_id': self.tech_user_2.id,
            'note': 'Cố tình chuyển việc cho người khác',
        })
        self.assertEqual(resp.status_code, 403)

        # Tech 1 tự gán cho chính mình (claim) -> Cho phép
        resp_self = client.post(reverse('tickets:assign', args=[self.ticket_1.id]), {
            'technician_id': self.tech_user_1.id,
            'note': 'Tôi tự nhận sự cố này',
        })
        self.assertEqual(resp_self.status_code, 302)
        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.assigned_to, self.tech_user_1)

    def test_admin_can_reassign_to_any_technician(self):
        client = Client()
        client.force_login(self.admin_user)

        # Admin gán ticket 1 cho Tech 2
        resp = client.post(reverse('tickets:assign', args=[self.ticket_1.id]), {
            'technician_id': self.tech_user_2.id,
            'note': 'Admin điều phối cho Tech Dũng',
        })
        self.assertEqual(resp.status_code, 302)
        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.assigned_to, self.tech_user_2)

        # Kiểm tra lịch sử
        history = TicketHistory.objects.filter(ticket=self.ticket_1).latest('created_at')
        self.assertEqual(history.assigned_to, self.tech_user_2)
        self.assertEqual(history.changed_by, self.admin_user)
        self.assertIn('Admin điều phối cho Tech Dũng', history.note)

    # --- Test Status Change & History ---
    def test_status_update_across_all_four_statuses(self):
        client = Client()
        client.force_login(self.admin_user)

        # 1. new -> in_progress
        client.post(reverse('tickets:change_status', args=[self.ticket_1.id]), {
            'status': 'in_progress',
            'note': 'Bắt đầu kiểm tra switch',
        })
        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, 'in_progress')

        # 2. in_progress -> resolved
        client.post(reverse('tickets:change_status', args=[self.ticket_1.id]), {
            'status': 'resolved',
            'note': 'Đã thay nguồn switch',
        })
        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, 'resolved')

        # 3. resolved -> closed
        client.post(reverse('tickets:change_status', args=[self.ticket_1.id]), {
            'status': 'closed',
            'note': 'Người dùng xác nhận mạng tốt',
        })
        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, 'closed')

        # 4. closed -> open / new
        client.post(reverse('tickets:change_status', args=[self.ticket_1.id]), {
            'status': 'open',
            'note': 'Mở lại ticket',
        })
        self.ticket_1.refresh_from_db()
        self.assertEqual(self.ticket_1.status, 'new')

        # Kiểm tra histories ghi nhận đầy đủ người thực hiện và ghi chú
        histories = TicketHistory.objects.filter(ticket=self.ticket_1)
        self.assertEqual(histories.count(), 4)

    # --- Test Reports View ---
    def test_reports_view_permissions_and_content(self):
        client = Client()

        # Regular user bị chặn 403
        client.force_login(self.regular_user)
        resp = client.get(reverse('tickets:reports'))
        self.assertEqual(resp.status_code, 403)

        # Admin xem được
        client.force_login(self.admin_user)
        resp = client.get(reverse('tickets:reports'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Báo Cáo &amp; Thống Kê Sự Cố Mạng')
        self.assertIn('tech_stats', resp.context)

