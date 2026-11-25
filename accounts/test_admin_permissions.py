"""Exercise account administration through real admin URLs and requests."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Role, UserProfile


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class AccountAdminPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user_role = Role.objects.get(name='user')
        cls.tech_role = Role.objects.get(name='technician')
        cls.admin_role = Role.objects.get(name='admin')
        cls.owner = User.objects.create_user(username='account-owner', password='OriginalPassword!842')
        cls.staff_user = User.objects.create_user(username='ordinary-staff', is_staff=True)
        cls.technician = User.objects.create_user(username='account-technician', is_staff=True)
        cls.technician.profile.role = cls.tech_role
        cls.technician.profile.save(update_fields=['role'])
        cls.administrator = User.objects.create_user(username='account-admin', is_staff=True)
        cls.administrator.profile.role = cls.admin_role
        cls.administrator.profile.save(update_fields=['role'])
        cls.superuser = User.objects.create_superuser(username='account-root', password='RootPassword!842')
        cls.group = Group.objects.create(name='Account administration test group')
        permissions = Permission.objects.filter(content_type__app_label__in=['accounts', 'auth'])
        for user in (cls.staff_user, cls.technician, cls.administrator):
            user.user_permissions.set(permissions)

    def targets(self):
        return (
            ('auth_user', self.owner),
            ('auth_group', self.group),
            ('accounts_role', self.user_role),
            ('accounts_userprofile', self.owner.profile),
        )

    def read_urls(self):
        for model, obj in self.targets():
            for action in ('changelist', 'add'):
                yield reverse(f'admin:{model}_{action}')
            for action in ('change', 'history', 'delete'):
                yield reverse(f'admin:{model}_{action}', args=[obj.pk])
        yield reverse('admin:auth_user_password_change', args=[self.owner.pk])

    def assert_reads_denied(self, user):
        self.client.force_login(user)
        for url in self.read_urls():
            with self.subTest(user=user.username, url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_anonymous_account_urls_require_login(self):
        for url in self.read_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('accounts:login') + '?next='))

    def test_normal_registered_account_cannot_enter_admin(self):
        self.client.force_login(self.owner)
        for url in self.read_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse('admin:login') + '?next='))

    def test_user_role_is_denied_even_with_staff_and_all_account_permissions(self):
        self.assert_reads_denied(self.staff_user)

    def test_technician_cannot_administer_accounts_even_with_django_permissions(self):
        self.assert_reads_denied(self.technician)

    def test_group_permissions_cannot_bypass_the_role_check(self):
        self.staff_user.user_permissions.clear()
        self.group.permissions.set(Permission.objects.filter(content_type__app_label__in=['accounts', 'auth']))
        self.staff_user.groups.add(self.group)
        self.assert_reads_denied(self.staff_user)

    def test_missing_profile_and_missing_role_are_denied(self):
        self.staff_user.profile.delete()
        self.assert_reads_denied(get_user_model().objects.get(pk=self.staff_user.pk))
        UserProfile.objects.create(user=self.staff_user, role=None)
        self.assert_reads_denied(get_user_model().objects.get(pk=self.staff_user.pk))

    def test_admin_role_does_not_bypass_staff_or_active_flags(self):
        for field in ('is_staff', 'is_active'):
            with self.subTest(field=field):
                setattr(self.administrator, field, False)
                self.administrator.save(update_fields=[field])
                self.client.force_login(self.administrator)
                response = self.client.get(reverse('admin:auth_user_changelist'))
                self.assertEqual(response.status_code, 302)
                setattr(self.administrator, field, True)
                self.administrator.save(update_fields=[field])

    def test_admin_role_still_needs_django_model_permissions(self):
        self.administrator.user_permissions.clear()
        self.assert_reads_denied(self.administrator)

    def test_admin_with_view_permission_cannot_post_changes_or_reset_passwords(self):
        self.administrator.user_permissions.set(Permission.objects.filter(
            content_type__app_label='auth', codename='view_user',
        ))
        self.client.force_login(self.administrator)
        change_url = reverse('admin:auth_user_change', args=[self.owner.pk])
        self.assertEqual(self.client.get(change_url).status_code, 200)
        before = self.owner.password
        urls = [change_url, reverse('admin:auth_user_add'),
                reverse('admin:auth_user_delete', args=[self.owner.pk]),
                reverse('admin:auth_user_password_change', args=[self.owner.pk])]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {'is_superuser': 'on'}).status_code, 403)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.password, before)
        self.assertFalse(self.owner.is_superuser)

    def test_post_cannot_change_user_flags_password_or_delete_user(self):
        self.client.force_login(self.staff_user)
        before = self.owner.password
        attempts = (
            ('auth_user_change', {'username': self.owner.username, 'is_staff': 'on', 'is_superuser': 'on', 'is_active': 'on'}),
            ('auth_user_password_change', {'password1': 'ChangedPassword!842', 'password2': 'ChangedPassword!842'}),
            ('auth_user_delete', {'post': 'yes'}),
        )
        for name, data in attempts:
            with self.subTest(name=name):
                self.assertEqual(self.client.post(reverse(f'admin:{name}', args=[self.owner.pk]), data).status_code, 403)
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_staff)
        self.assertFalse(self.owner.is_superuser)
        self.assertEqual(self.owner.password, before)

    def test_post_cannot_add_users_roles_profiles_or_groups(self):
        self.client.force_login(self.staff_user)
        counts = tuple(model.objects.count() for model in (get_user_model(), Role, UserProfile, Group))
        payloads = (
            ('auth_user', {'username': 'unauthorized-user', 'password1': 'AnotherPassword!842', 'password2': 'AnotherPassword!842'}),
            ('auth_group', {'name': 'unauthorized-group'}),
            ('accounts_role', {'name': 'unauthorized-role', 'description': 'Not allowed'}),
            ('accounts_userprofile', {'user': self.owner.pk, 'role': self.admin_role.pk}),
        )
        for model, data in payloads:
            with self.subTest(model=model):
                self.assertEqual(self.client.post(reverse(f'admin:{model}_add'), data).status_code, 403)
        self.assertEqual(tuple(model.objects.count() for model in (get_user_model(), Role, UserProfile, Group)), counts)

    def test_post_cannot_escalate_profiles_or_edit_roles_and_groups(self):
        self.client.force_login(self.staff_user)
        requests = (
            ('accounts_userprofile', self.owner.profile, {'user': self.owner.pk, 'role': self.admin_role.pk, 'phone': '', 'department': ''}),
            ('accounts_role', self.user_role, {'name': 'admin', 'description': 'Escalation'}),
            ('auth_group', self.group, {'name': 'Escalated group', 'permissions': list(Permission.objects.values_list('pk', flat=True))}),
        )
        for model, obj, data in requests:
            with self.subTest(model=model):
                self.assertEqual(self.client.post(reverse(f'admin:{model}_change', args=[obj.pk]), data).status_code, 403)
        self.owner.profile.refresh_from_db()
        self.user_role.refresh_from_db()
        self.group.refresh_from_db()
        self.assertEqual(self.owner.profile.role_id, self.user_role.pk)
        self.assertEqual(self.user_role.name, 'user')
        self.assertEqual(self.group.name, 'Account administration test group')
        self.assertFalse(self.group.permissions.exists())

    def test_bulk_delete_actions_are_denied_without_deleting_accounts(self):
        self.client.force_login(self.staff_user)
        for model, obj in self.targets():
            with self.subTest(model=model):
                response = self.client.post(reverse(f'admin:{model}_changelist'), {
                    'action': 'delete_selected', '_selected_action': [obj.pk], 'post': 'yes',
                })
                self.assertEqual(response.status_code, 403)
                self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())

    def test_autocomplete_does_not_disclose_account_results(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('admin:autocomplete'), {
            'app_label': 'tickets', 'model_name': 'ticket', 'field_name': 'created_by', 'term': 'account',
        })
        self.assertEqual(response.status_code, 403)

    def test_account_modules_are_not_listed_for_user_or_technician(self):
        for user in (self.staff_user, self.technician):
            self.client.force_login(user)
            response = self.client.get(reverse('admin:index'))
            self.assertEqual(response.status_code, 200)
            for model, _ in self.targets():
                self.assertNotContains(response, f'href="{reverse(f"admin:{model}_changelist")}"')

    def test_admin_with_permissions_and_superuser_keep_account_access(self):
        for user in (self.administrator, self.superuser):
            self.client.force_login(user)
            for url in self.read_urls():
                if url.endswith('/delete/'):
                    continue
                with self.subTest(user=user.username, url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_authorized_admin_can_save_profile_and_create_group(self):
        self.client.force_login(self.administrator)
        response = self.client.post(reverse('admin:accounts_userprofile_change', args=[self.owner.profile.pk]), {
            'user': self.owner.pk, 'role': self.tech_role.pk, 'phone': '0900000000', 'department': 'CNTT',
        })
        self.assertEqual(response.status_code, 302)
        self.owner.profile.refresh_from_db()
        self.assertEqual(self.owner.profile.role_id, self.tech_role.pk)
        response = self.client.post(reverse('admin:auth_group_add'), {'name': 'Authorized support group'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Group.objects.filter(name='Authorized support group').exists())

    def test_removing_admin_role_takes_effect_on_the_next_request(self):
        self.client.force_login(self.administrator)
        url = reverse('admin:auth_user_changelist')
        self.assertEqual(self.client.get(url).status_code, 200)
        UserProfile.objects.filter(user=self.administrator).update(role=self.user_role)
        self.assertEqual(self.client.get(url).status_code, 403)
