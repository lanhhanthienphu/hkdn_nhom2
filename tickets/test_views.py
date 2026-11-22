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

    def test_edit_ticket_permissions_and_history(self):
        ticket = Ticket.objects.create(
            title='Lỗi Wi-Fi ban đầu tại A.101',
            category='network',
            priority='normal',
            location='A.101',
            description='Không thể truy cập Internet từ đầu buổi sáng nay.',
            created_by=self.user_reporter,
        )
        edit_url = reverse('tickets:edit', args=[ticket.id])
        updated_payload = {
            'title': 'Lỗi Wi-Fi đã cập nhật tại A.202',
            'category': 'vpn',
            'priority': 'urgent',
            'location': 'A.202',
            'description': 'Cập nhật lại mô tả chi tiết hơn về lỗi mạng VPN và Wi-Fi.',
        }

        # Other user gets 404
        client_other = Client()
        client_other.force_login(self.user_other)
        self.assertEqual(client_other.get(edit_url).status_code, 404)

        # Creator can GET and POST while new & unassigned
        client_rep = Client()
        client_rep.force_login(self.user_reporter)
        self.assertEqual(client_rep.get(edit_url).status_code, 200)
        resp = client_rep.post(edit_url, updated_payload)
        self.assertRedirects(resp, reverse('tickets:detail', args=[ticket.id]))
        ticket.refresh_from_db()
        self.assertEqual(ticket.title, updated_payload['title'])
        self.assertEqual(ticket.priority, 'urgent')
        self.assertEqual(ticket.histories.count(), 1)

        # Once assigned, creator can no longer edit (403), but tech can
        ticket.assign_technician(self.user_tech, by=self.user_tech)
        self.assertEqual(client_rep.get(edit_url).status_code, 403)
        self.assertEqual(client_rep.post(edit_url, updated_payload).status_code, 403)

        client_tech = Client()
        client_tech.force_login(self.user_tech)
        self.assertEqual(client_tech.get(edit_url).status_code, 200)

    def test_delete_ticket_permissions(self):
        admin_user = User.objects.create_user(username='admin_del', password='Password_123!')
        admin_user.profile.role = self.role_admin
        admin_user.profile.save()

        # 1. Creator deletes own new unassigned ticket
        t1 = Ticket.objects.create(
            title='Ticket tạo nhầm cần xóa',
            category='other',
            priority='low',
            location='B.101',
            description='Mô tả chi tiết sự cố tạo nhầm cần xóa ngay.',
            created_by=self.user_reporter,
        )
        client_rep = Client()
        client_rep.force_login(self.user_reporter)
        resp = client_rep.post(reverse('tickets:delete', args=[t1.id]))
        self.assertRedirects(resp, reverse('tickets:list'))
        self.assertFalse(Ticket.objects.filter(pk=t1.id).exists())

        # 2. Assigned ticket: creator & tech get 403, other gets 404, admin deletes successfully
        t2 = Ticket.objects.create(
            title='Ticket đang xử lý',
            category='network',
            priority='high',
            location='B.102',
            description='Mô tả chi tiết sự cố đang được xử lý.',
            created_by=self.user_reporter,
            assigned_to=self.user_tech,
            status='in_progress',
        )
        del_url = reverse('tickets:delete', args=[t2.id])
        self.assertEqual(client_rep.post(del_url).status_code, 403)

        client_tech = Client()
        client_tech.force_login(self.user_tech)
        self.assertEqual(client_tech.post(del_url).status_code, 403)

        client_other = Client()
        client_other.force_login(self.user_other)
        self.assertEqual(client_other.post(del_url).status_code, 404)

        client_admin = Client()
        client_admin.force_login(admin_user)
        resp_admin = client_admin.post(del_url)
        self.assertRedirects(resp_admin, reverse('tickets:list'))
        self.assertFalse(Ticket.objects.filter(pk=t2.id).exists())

    def test_unassign_and_closed_ticket_assignment_guard(self):
        admin_user = User.objects.create_user(username='admin_unassign', password='Password_123!')
        admin_user.profile.role = self.role_admin
        admin_user.profile.save()

        ticket = Ticket.objects.create(
            title='Sự cố cần điều phối lại',
            category='network',
            priority='high',
            location='A.301',
            description='Mất kết nối switch tầng 3.',
            created_by=self.user_reporter,
            assigned_to=self.user_tech,
            status='in_progress',
        )
        unassign_url = reverse('tickets:unassign', args=[ticket.id])

        # Non-admin tech cannot unassign
        client_tech = Client()
        client_tech.force_login(self.user_tech)
        self.assertEqual(client_tech.post(unassign_url).status_code, 403)

        # Admin unassigns cleanly
        client_admin = Client()
        client_admin.force_login(admin_user)
        resp = client_admin.post(unassign_url, {'note': 'Chuyển nhóm xử lý'})
        self.assertRedirects(resp, reverse('tickets:detail', args=[ticket.id]))
        ticket.refresh_from_db()
        self.assertIsNone(ticket.assigned_to)
        self.assertEqual(ticket.histories.latest('created_at').note, 'Chuyển nhóm xử lý')

        # Closed ticket rejects assignment
        ticket.change_status('closed', by=admin_user)
        resp_closed = client_admin.post(
            reverse('tickets:assign', args=[ticket.id]),
            {'technician_id': self.user_tech.id},
            follow=True,
        )
        self.assertContains(resp_closed, 'Không thể phân công kỹ thuật viên cho ticket đã đóng')
        ticket.refresh_from_db()
        self.assertIsNone(ticket.assigned_to)

    def test_open_redirect_blocked_on_assign_and_status(self):
        ticket = Ticket.objects.create(
            title='Kiểm tra open redirect',
            category='network',
            priority='normal',
            location='A.101',
            description='Mô tả sự cố kiểm tra chuyển hướng an toàn.',
            created_by=self.user_reporter,
        )
        client_tech = Client()
        client_tech.force_login(self.user_tech)
        detail_url = reverse('tickets:detail', args=[ticket.id])

        for malicious_next in ('//evil.com/phish', 'https://evil.com/phish', '/\\evil.com'):
            resp_assign = client_tech.post(reverse('tickets:assign', args=[ticket.id]), {
                'technician_id': self.user_tech.id,
                'next': malicious_next,
            })
            self.assertEqual(resp_assign.status_code, 302)
            self.assertEqual(resp_assign.url, detail_url)

            resp_status = client_tech.post(reverse('tickets:change_status', args=[ticket.id]), {
                'status': 'resolved',
                'next': malicious_next,
            })
            self.assertEqual(resp_status.status_code, 302)
            self.assertEqual(resp_status.url, detail_url)

    def test_case_insensitive_technician_queryset_and_closed_detail_flag(self):
        from tickets.views import get_technicians_queryset
        role_upper = Role.objects.create(name='Technician', description='Viết hoa chữ đầu')
        upper_tech = User.objects.create_user(username='upper_tech', password='Password_123!')
        upper_tech.profile.role = role_upper
        upper_tech.profile.save()
        self.assertIn(upper_tech, list(get_technicians_queryset()))

        closed_ticket = Ticket.objects.create(
            title='Ticket đã đóng cho user',
            category='network',
            priority='low',
            location='A.100',
            description='Mô tả chi tiết sự cố đã đóng.',
            status='closed',
            created_by=self.user_reporter,
        )
        client_rep = Client()
        client_rep.force_login(self.user_reporter)
        resp = client_rep.get(reverse('tickets:detail', args=[closed_ticket.id]))
        self.assertFalse(resp.context['can_change_status'])
        self.assertFalse(resp.context['can_edit'])
        self.assertFalse(resp.context['can_delete'])

