from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role, UserProfile
from tickets.models import Comment, Ticket, TicketHistory

User = get_user_model()


class TicketViewsDBTests(TestCase):
    def setUp(self):
        # Create roles
        self.role_admin = Role.objects.get_or_create(name='admin', defaults={'description': 'Quản trị viên'})[0]
        self.role_tech = Role.objects.get_or_create(name='technician', defaults={'description': 'Kỹ thuật viên'})[0]
        self.role_user = Role.objects.get_or_create(name='user', defaults={'description': 'Người dùng'})[0]

        # Create users
        self.user_reporter = User.objects.create_user(username='reporter_db', password='Password_123!')
        self.user_reporter.profile.role = self.role_user
        self.user_reporter.profile.save()

        self.user_tech = User.objects.create_user(username='tech_db', password='Password_123!')
        self.user_tech.profile.role = self.role_tech
        self.user_tech.profile.save()

        self.user_other = User.objects.create_user(username='other_db', password='Password_123!')
        self.user_other.profile.role = self.role_user
        self.user_other.profile.save()

        self.ticket_data = {
            'title': 'Không kết nối được Wi-Fi phòng B.102',
            'category': 'network',
            'priority': 'high',
            'location': 'B.102',
            'description': 'Mạng bị rớt liên tục trong suốt 1 tiếng qua.',
        }

    def test_create_ticket_saves_to_db(self):
        client = Client()
        client.force_login(self.user_reporter)

        response = client.post(reverse('tickets:create'), self.ticket_data)
        self.assertEqual(response.status_code, 302)

        ticket = Ticket.objects.get(title=self.ticket_data['title'])
        self.assertEqual(ticket.created_by, self.user_reporter)
        self.assertEqual(ticket.status, 'new')
        self.assertEqual(ticket.location, 'B.102')

        # Check history was created
        history = TicketHistory.objects.filter(ticket=ticket)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().changed_by, self.user_reporter)

    def test_list_tickets_permission_isolation(self):
        t1 = Ticket.objects.create(
            title='Ticket của reporter',
            category='network',
            priority='normal',
            location='A.101',
            description='Chi tiết sự cố của reporter',
            created_by=self.user_reporter,
        )
        t2 = Ticket.objects.create(
            title='Ticket của người khác',
            category='vpn',
            priority='high',
            location='B.202',
            description='Chi tiết sự cố của other',
            created_by=self.user_other,
        )

        # Reporter client
        client_rep = Client()
        client_rep.force_login(self.user_reporter)
        resp = client_rep.get(reverse('tickets:list'))
        tickets_in_view = list(resp.context['page_obj'])
        self.assertIn(t1, tickets_in_view)
        self.assertNotIn(t2, tickets_in_view)

        # Tech client can view all
        client_tech = Client()
        client_tech.force_login(self.user_tech)
        resp_tech = client_tech.get(reverse('tickets:list'))
        tickets_tech_view = list(resp_tech.context['page_obj'])
        self.assertIn(t1, tickets_tech_view)
        self.assertIn(t2, tickets_tech_view)

    def test_detail_view_permissions_and_comments(self):
        ticket = Ticket.objects.create(
            title='Sự cố máy in thư viện',
            category='printer',
            priority='normal',
            location='Thư viện',
            description='Máy in kẹt giấy liên tục và báo lỗi đỏ.',
            created_by=self.user_reporter,
        )

        client_other = Client()
        client_other.force_login(self.user_other)
        resp_404 = client_other.get(reverse('tickets:detail', args=[ticket.id]))
        self.assertEqual(resp_404.status_code, 404)

        client_rep = Client()
        client_rep.force_login(self.user_reporter)
        resp_200 = client_rep.get(reverse('tickets:detail', args=[ticket.id]))
        self.assertEqual(resp_200.status_code, 200)

        # Add comment
        resp_comment = client_rep.post(reverse('tickets:detail', args=[ticket.id]), {
            'content': 'Em đã mở nắp máy in kiểm tra và lấy giấy kẹt ra rồi nhưng đèn vẫn đỏ.'
        })
        self.assertEqual(resp_comment.status_code, 302)
        self.assertEqual(Comment.objects.filter(ticket=ticket).count(), 1)

    def test_cannot_comment_on_closed_ticket(self):
        ticket = Ticket.objects.create(
            title='Ticket đã đóng',
            category='network',
            priority='low',
            location='A.100',
            description='Mô tả chi tiết',
            status='closed',
            created_by=self.user_reporter,
        )
        client = Client()
        client.force_login(self.user_reporter)
        resp = client.post(reverse('tickets:detail', args=[ticket.id]), {
            'content': 'Thử bình luận vào ticket đã đóng'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Ticket đã đóng', str(resp.context['form'].non_field_errors()))
        self.assertEqual(Comment.objects.filter(ticket=ticket).count(), 0)

    def test_technician_assignment_and_status_flow(self):
        ticket = Ticket.objects.create(
            title='Sự cố mạng LAN phòng giáo viên',
            category='network',
            priority='urgent',
            location='Phòng 301',
            description='Cả phòng mất kết nối Internet nội bộ.',
            created_by=self.user_reporter,
        )

        client_tech = Client()
        client_tech.force_login(self.user_tech)

        # Assign technician
        resp_assign = client_tech.post(reverse('tickets:assign', args=[ticket.id]), {
            'technician_id': self.user_tech.id,
            'note': 'Kỹ thuật viên tiếp nhận xử lý',
        })
        self.assertEqual(resp_assign.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.assigned_to, self.user_tech)
        self.assertEqual(ticket.status, 'in_progress')

        # Update status to resolved
        resp_status = client_tech.post(reverse('tickets:change_status', args=[ticket.id]), {
            'status': 'resolved',
            'note': 'Đã thay switch mạng mới',
        })
        self.assertEqual(resp_status.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'resolved')

        # Check TicketHistory entries
        histories = TicketHistory.objects.filter(ticket=ticket)
        self.assertEqual(histories.count(), 2)

    def test_regular_user_cannot_assign_or_change_status(self):
        ticket = Ticket.objects.create(
            title='Sự cố VPN',
            category='vpn',
            priority='normal',
            location='Văn phòng',
            description='Không kết nối được VPN.',
            created_by=self.user_reporter,
        )

        client_rep = Client()
        client_rep.force_login(self.user_reporter)

        resp_assign = client_rep.post(reverse('tickets:assign', args=[ticket.id]), {
            'technician_id': self.user_reporter.id,
        })
        self.assertEqual(resp_assign.status_code, 403)

        resp_status = client_rep.post(reverse('tickets:change_status', args=[ticket.id]), {
            'status': 'resolved',
        })
        self.assertEqual(resp_status.status_code, 403)

