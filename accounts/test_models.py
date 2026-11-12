from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Role, UserProfile

User = get_user_model()


class RoleAndUserProfileModelTests(TestCase):
    def setUp(self):
        self.role_admin = Role.objects.get_or_create(name='admin', defaults={'description': 'Quản trị viên'})[0]
        self.role_tech = Role.objects.get_or_create(name='technician', defaults={'description': 'Kỹ thuật viên'})[0]
        self.role_user = Role.objects.get_or_create(name='user', defaults={'description': 'Người dùng cuối'})[0]

        self.user1 = User.objects.create_user(username='u_admin', password='passWord123!')
        self.user2 = User.objects.create_user(username='u_tech', password='passWord123!')
        self.user3 = User.objects.create_user(username='u_normal', password='passWord123!')

        self.profile1 = self.user1.profile
        self.profile1.role = self.role_admin
        self.profile1.phone = '0901234567'
        self.profile1.department = 'Phòng CNTT'
        self.profile1.save()

        self.profile2 = self.user2.profile
        self.profile2.role = self.role_tech
        self.profile2.phone = '0902345678'
        self.profile2.department = 'Tổ Hỗ Trợ Kỹ Thuật'
        self.profile2.save()

        self.profile3 = self.user3.profile
        self.profile3.role = self.role_user
        self.profile3.phone = '0903456789'
        self.profile3.department = 'Phòng Đào Tạo'
        self.profile3.save()

    def test_role_str(self):
        self.assertEqual(str(self.role_admin), 'admin')

    def test_profile_str(self):
        self.assertIn('u_admin', str(self.profile1))
        self.assertIn('admin', str(self.profile1))

    def test_role_check_methods(self):
        self.assertTrue(self.profile1.is_admin())
        self.assertTrue(self.profile1.is_technician())  # Admin also has tech capabilities
        self.assertFalse(self.profile1.is_end_user())

        self.assertFalse(self.profile2.is_admin())
        self.assertTrue(self.profile2.is_technician())
        self.assertFalse(self.profile2.is_end_user())

        self.assertFalse(self.profile3.is_admin())
        self.assertFalse(self.profile3.is_technician())
        self.assertTrue(self.profile3.is_end_user())
