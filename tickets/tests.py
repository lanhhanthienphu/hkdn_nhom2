from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .demo_store import MAX_REPLIES, MAX_TICKETS, SESSION_KEY
from .forms import MAX_ATTACHMENT_BYTES, TicketForm


@override_settings(FRONTEND_DEMO_ENABLED=True)
class FrontendTicketTests(TestCase):
    def setUp(self):
        self.data = {
            'title': 'Wi-Fi không kết nối được tại A.201', 'category': 'network',
            'priority': 'high', 'location': 'A.201',
            'description': 'Sự cố xảy ra lúc đầu giờ học. Đã thử kết nối lại nhưng vẫn chưa truy cập được Internet.',
        }

    def test_navigation_and_category_location_prefill(self):
        response = self.client.get(reverse('tickets:home'))
        self.assertContains(response, reverse('tickets:create'))
        response = self.client.get(reverse('tickets:create'), {'category': 'vpn', 'location': 'B.302'})
        self.assertEqual(response.context['form']['category'].value(), 'vpn')
        self.assertEqual(response.context['form']['location'].value(), 'B.302')
        self.assertContains(response, 'chưa gửi đến bộ phận kỹ thuật')

    def test_create_redirects_and_persists_in_same_browser_only(self):
        response = self.client.post(reverse('tickets:create'), self.data)
        url = reverse('tickets:detail', args=[1007])
        self.assertRedirects(response, url)
        self.assertContains(self.client.get(url), self.data['title'])
        response = self.client.get(reverse('tickets:list'), {'q': 'HD-1007'})
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        self.assertEqual(Client().get(url).status_code, 404)
        self.assertEqual(len(self.client.session[SESSION_KEY]), 7)

    def test_invalid_form_keeps_values_and_does_not_create_ticket(self):
        response = self.client.post(reverse('tickets:create'), {**self.data, 'description': 'ngắn', 'category': 'bad'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('description', response.context['form'].errors)
        self.assertIn('category', response.context['form'].errors)
        self.assertEqual(response.context['form']['title'].value(), self.data['title'])
        self.assertEqual(len(self.client.session[SESSION_KEY]), 6)

    def test_attachment_checks_size_extension_and_keeps_metadata_only(self):
        bad = TicketForm(self.data, {'attachment': SimpleUploadedFile('run.exe', b'bad')})
        self.assertFalse(bad.is_valid())
        self.assertIn('attachment', bad.errors)
        large = SimpleUploadedFile('large.pdf', b'x' * (MAX_ATTACHMENT_BYTES + 1))
        self.assertFalse(TicketForm(self.data, {'attachment': large}).is_valid())
        response = self.client.post(reverse('tickets:create'), {
            **self.data, 'attachment': SimpleUploadedFile('network.LOG', b'connection timed out'),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session[SESSION_KEY][-1]['attachment'], {'name': 'network.LOG', 'size': 20})
        self.assertContains(self.client.get(response.url), 'chưa có nội dung để tải')

    def test_filters_sorting_pagination_and_empty_result(self):
        url = reverse('tickets:list')
        response = self.client.get(url, {'q': 'A.201', 'category': 'network', 'status': 'in_progress'})
        self.assertEqual([t['id'] for t in response.context['page_obj']], [1006])
        response = self.client.get(url, {'sort': 'oldest'})
        self.assertEqual(response.context['page_obj'][0]['id'], 1001)
        self.assertContains(response, 'sort=oldest&amp;page=2')
        self.assertEqual(len(self.client.get(url, {'page': 2}).context['page_obj']), 1)
        response = self.client.get(url, {'sort': 'priority'})
        self.assertEqual(response.context['page_obj'][0]['priority'], 'urgent')
        self.assertContains(self.client.get(url, {'q': 'does-not-exist'}), 'Không tìm thấy ticket phù hợp')
        self.assertEqual(self.client.get(url, {'page': 'invalid', 'status': 'unknown'}).status_code, 200)

    def test_empty_ticket_state(self):
        session = self.client.session
        session[SESSION_KEY] = []
        session.save()
        self.assertContains(self.client.get(reverse('tickets:list')), 'Bạn chưa có ticket nào')

    def test_reply_post_redirect_get_and_escaping(self):
        url = reverse('tickets:detail', args=[1006])
        message = '<script>alert("test")</script> Kết nối vẫn bị gián đoạn.'
        response = self.client.post(url, {'content': message})
        self.assertRedirects(response, url + '#conversation')
        response = self.client.get(url)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(')
        self.assertEqual(len(response.context['ticket']['replies']), 2)
        self.assertEqual(len(self.client.get(url).context['ticket']['replies']), 2)

    def test_closed_ticket_rejects_replies_and_missing_ticket_is_404(self):
        url = reverse('tickets:detail', args=[1002])
        before = self.client.get(url).context['ticket']['replies']
        response = self.client.post(url, {'content': 'Nội dung không được thêm'})
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertEqual(self.client.get(url).context['ticket']['replies'], before)
        self.assertNotContains(self.client.get(url), 'name="content"')
        self.assertEqual(self.client.get(reverse('tickets:detail', args=[9999])).status_code, 404)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse('tickets:create'))
        self.assertEqual(client.post(reverse('tickets:create'), self.data).status_code, 403)
        response = client.post(reverse('tickets:create'), {
            **self.data, 'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        })
        self.assertEqual(response.status_code, 302)

    def test_demo_limits_are_enforced(self):
        self.client.get(reverse('tickets:list'))
        session = self.client.session
        seed = session[SESSION_KEY][0]
        session[SESSION_KEY] = [{**seed, 'id': 2000 + i} for i in range(MAX_TICKETS)]
        session.save()
        response = self.client.post(reverse('tickets:create'), self.data)
        self.assertTrue(response.context['form'].non_field_errors())
        session = self.client.session
        records = session[SESSION_KEY]
        records[0]['replies'] = seed['replies'] * MAX_REPLIES
        session[SESSION_KEY] = records
        session.save()
        response = self.client.post(reverse('tickets:detail', args=[2000]), {'content': 'Phản hồi thử giới hạn'})
        self.assertTrue(response.context['form'].non_field_errors())

    @override_settings(FRONTEND_DEMO_ENABLED=False)
    def test_disabled_demo_routes_return_404(self):
        for name in ('list', 'create'):
            self.assertEqual(self.client.get(reverse(f'tickets:{name}')).status_code, 404)
        self.assertEqual(self.client.get(reverse('tickets:detail', args=[1006])).status_code, 404)
