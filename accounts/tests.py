from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(FRONTEND_DEMO_ENABLED=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FrontendAccountIntegrationTests(TestCase):
    def setUp(self):
        self.password = 'FrontendCheck!9371'
        self.user = get_user_model().objects.create_user(username='khoi-test', email='khoi-test@example.test', password=self.password)

    def test_anonymous_redirect_keeps_location_and_category(self):
        target = '/tickets/new/?location=A.201&category=network'
        response = self.client.get(target)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(parse_qs(urlsplit(response.url).query)['next'], [target])
        response = self.client.post(reverse('accounts:login'), {'username': self.user.username, 'password': self.password, 'next': target})
        self.assertRedirects(response, target)
        form = self.client.get(target).context['form']
        self.assertEqual(form['location'].value(), 'A.201')
        self.assertEqual(form['category'].value(), 'network')

    def test_invalid_login_preserves_next_and_has_accessible_errors(self):
        response = self.client.post(reverse('accounts:login'), {'username': self.user.username, 'password': 'wrong', 'next': '/tickets/new/?location=A.201'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertContains(response, 'Tên đăng nhập hoặc mật khẩu không đúng')
        self.assertContains(response, 'data-error-summary')
        self.assertContains(response, 'value="/tickets/new/?location=A.201"')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_does_not_redirect_to_external_sites(self):
        response = self.client.post(reverse('accounts:login'), {'username': self.user.username, 'password': self.password, 'next': 'https://external.invalid/path'})
        self.assertRedirects(response, reverse('tickets:home'))

    def test_register_returns_to_safe_next_and_cannot_set_staff_flags(self):
        target = '/tickets/new/?location=B.302&category=printer'
        response = self.client.post(reverse('accounts:register'), {
            'username': 'new-frontend-user', 'email': 'frontend@example.test',
            'password1': self.password, 'password2': self.password, 'next': target,
            'is_staff': 'true', 'is_superuser': 'true',
        })
        self.assertRedirects(response, target)
        user = get_user_model().objects.get(username='new-frontend-user')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_rejects_unsafe_next_and_invalid_fields(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'valid-new-user', 'email': 'new@example.test',
            'password1': self.password, 'password2': self.password, 'next': '//external.invalid',
        })
        self.assertRedirects(response, reverse('tickets:home'))
        self.client.logout()
        response = self.client.post(reverse('accounts:register'), {
            'username': 'bad name!', 'email': 'not-an-email', 'password1': 'x', 'password2': 'y',
        })
        self.assertIn('username', response.context['form'].errors)
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(get_user_model().objects.count(), 2)

    def test_logout_requires_post_and_header_links_to_kb(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('tickets:home'))
        self.assertContains(response, 'method="post" action="/accounts/logout/"')
        self.assertContains(response, reverse('kb:article_list'))
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post(reverse('accounts:logout')), reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('tickets:list')).status_code, 302)

    def test_csrf_failure_is_a_friendly_page_and_does_not_log_in(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse('accounts:login'), {'username': self.user.username, 'password': self.password})
        self.assertContains(response, 'Phiên làm việc cần được làm mới', status_code=403)
        self.assertNotContains(response, self.password, status_code=403)
        self.assertNotIn('_auth_user_id', client.session)

    def test_local_assets_and_responsive_login_markup(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'name="viewport"')
        self.assertContains(response, '/static/vendor/bootstrap/bootstrap.min.css')
        self.assertContains(response, 'autocomplete="current-password"')
        self.assertNotContains(response, 'cdn.jsdelivr.net')
