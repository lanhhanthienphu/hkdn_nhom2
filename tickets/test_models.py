from django.contrib.auth import get_user_model
from django.test import TestCase
from accounts.models import Role, UserProfile
from tickets.models import Comment, Ticket, TicketHistory

User = get_user_model()


class TicketModelTests(TestCase):
    def setUp(self):
        self.role_tech = Role.objects.get_or_create(name='technician')[0]
        self.role_user = Role.objects.get_or_create(name='user')[0]

        self.user_reporter = User.objects.create_user(username='reporter1', password='passWord123!')
        self.user_reporter.profile.role = self.role_user
        self.user_reporter.profile.save()

        self.user_tech = User.objects.create_user(username='tech1', password='passWord123!')
        self.user_tech.profile.role = self.role_tech
        self.user_tech.profile.save()

        self.user_other = User.objects.create_user(username='other_user', password='passWord123!')
        self.user_other.profile.role = self.role_user
        self.user_other.profile.save()

        self.ticket = Ticket.objects.create(
            title='Mất kết nối Wi-Fi tại A.201',
            category='network',
            priority='high',
            location='A.201',
            description='Không thể kết nối Internet từ sáng.',
            created_by=self.user_reporter,
        )

    def test_get_code_and_str(self):
        self.assertEqual(self.ticket.get_code(), f"HD-{self.ticket.id}")
        self.assertEqual(str(self.ticket), f"HD-{self.ticket.id} - Mất kết nối Wi-Fi tại A.201")
        self.assertEqual(self.ticket.code, f"HD-{self.ticket.id}")

    def test_default_status(self):
        self.assertEqual(self.ticket.status, 'new')

    def test_assign_technician_creates_history(self):
        self.ticket.assign_technician(self.user_tech, by=self.user_tech, note='Tiếp nhận xử lý')
        self.assertEqual(self.ticket.assigned_to, self.user_tech)
        self.assertEqual(self.ticket.status, 'in_progress')

        history = TicketHistory.objects.filter(ticket=self.ticket).latest('created_at')
        self.assertEqual(history.assigned_to, self.user_tech)
        self.assertEqual(history.changed_by, self.user_tech)
        self.assertEqual(history.new_status, 'in_progress')
        self.assertEqual(history.note, 'Tiếp nhận xử lý')

    def test_change_status_creates_history(self):
        self.ticket.change_status('resolved', by=self.user_tech, note='Đã sửa xong cáp mạng')
        self.assertEqual(self.ticket.status, 'resolved')

        history = TicketHistory.objects.filter(ticket=self.ticket).latest('created_at')
        self.assertEqual(history.old_status, 'new')
        self.assertEqual(history.new_status, 'resolved')
        self.assertEqual(history.note, 'Đã sửa xong cáp mạng')

    def test_can_view_permissions(self):
        # Reporter can view
        self.assertTrue(self.ticket.can_view(self.user_reporter))
        # Assigned tech can view
        self.ticket.assigned_to = self.user_tech
        self.ticket.save()
        self.assertTrue(self.ticket.can_view(self.user_tech))
        # Tech role can view any ticket
        self.assertTrue(self.ticket.can_view(self.user_tech))
        # Another standard user cannot view
        self.assertFalse(self.ticket.can_view(self.user_other))

    def test_comment_creation(self):
        comment = Comment.objects.create(
            ticket=self.ticket,
            user=self.user_reporter,
            content='Em đã khởi động lại router nhưng vẫn không được.',
        )
        self.assertEqual(comment.ticket, self.ticket)
        self.assertEqual(comment.user, self.user_reporter)
        self.assertIn('reporter1', str(comment))
