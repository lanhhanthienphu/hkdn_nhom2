from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
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

    def test_assign_and_unassign_closed_ticket_rejected(self):
        self.ticket.change_status('closed', by=self.user_tech)
        with self.assertRaises(ValidationError):
            self.ticket.assign_technician(self.user_tech, by=self.user_tech)
        with self.assertRaises(ValidationError):
            self.ticket.unassign_technician(by=self.user_tech)

    def test_unassign_technician_clears_assignee_and_logs_history(self):
        self.ticket.assign_technician(self.user_tech, by=self.user_tech)
        self.assertTrue(self.ticket.unassign_technician(by=self.user_tech, note='Đổi ca trực'))
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_to)
        # Second unassign is a no-op
        self.assertFalse(self.ticket.unassign_technician(by=self.user_tech))
        latest = self.ticket.histories.latest('created_at')
        self.assertIsNone(latest.assigned_to)
        self.assertEqual(latest.note, 'Đổi ca trực')

    def test_update_details_records_history_and_skips_noop(self):
        changed = self.ticket.update_details(
            data={'title': 'Tiêu đề mới sau chỉnh sửa', 'priority': 'urgent'},
            by=self.user_reporter,
        )
        self.assertEqual(changed, ['title', 'priority'])
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.title, 'Tiêu đề mới sau chỉnh sửa')
        self.assertEqual(self.ticket.priority, 'urgent')
        latest = self.ticket.histories.latest('created_at')
        self.assertIn('Tiêu đề', latest.note)
        self.assertIn('Độ ưu tiên', latest.note)

        # No-op update does not add duplicate history
        count_before = self.ticket.histories.count()
        self.assertEqual(
            self.ticket.update_details(data={'title': 'Tiêu đề mới sau chỉnh sửa'}, by=self.user_reporter),
            [],
        )
        self.assertEqual(self.ticket.histories.count(), count_before)

    def test_events_does_not_duplicate_creation_history(self):
        TicketHistory.objects.create(
            ticket=self.ticket,
            changed_by=self.user_reporter,
            old_status='',
            new_status='new',
            note='Đã tạo yêu cầu hỗ trợ sự cố',
        )
        events = self.ticket.events
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['title'], 'Đã tạo yêu cầu hỗ trợ sự cố')

    def test_can_edit_and_can_delete_permissions(self):
        role_admin = Role.objects.get_or_create(name='admin')[0]
        user_admin = User.objects.create_user(username='admin_model_test', password='passWord123!')
        user_admin.profile.role = role_admin
        user_admin.profile.save()

        # New & unassigned: creator can edit and delete; tech can edit only; admin can both; other neither
        self.assertTrue(self.ticket.can_edit(self.user_reporter))
        self.assertTrue(self.ticket.can_delete(self.user_reporter))
        self.assertTrue(self.ticket.can_edit(self.user_tech))
        self.assertFalse(self.ticket.can_delete(self.user_tech))
        self.assertTrue(self.ticket.can_edit(user_admin))
        self.assertTrue(self.ticket.can_delete(user_admin))
        self.assertFalse(self.ticket.can_edit(self.user_other))
        self.assertFalse(self.ticket.can_delete(self.user_other))

        # After assignment: creator can no longer edit or delete
        self.ticket.assign_technician(self.user_tech, by=user_admin)
        self.assertFalse(self.ticket.can_edit(self.user_reporter))
        self.assertFalse(self.ticket.can_delete(self.user_reporter))

        # After closed: tech can no longer edit; admin still can
        self.ticket.change_status('closed', by=user_admin)
        self.assertFalse(self.ticket.can_edit(self.user_tech))
        self.assertTrue(self.ticket.can_edit(user_admin))
        self.assertTrue(self.ticket.can_delete(user_admin))
