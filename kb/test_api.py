from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Article


class KnowledgeBaseAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="kb_api_user")
        cls.published = Article.objects.create(
            title="Hướng dẫn Wi-Fi",
            content="Kiểm tra kết nối mạng.",
            is_published=True,
        )
        cls.content_match = Article.objects.create(
            title="Kết nối từ xa",
            content="Kiểm tra cấu hình VPN.",
            is_published=True,
        )
        cls.draft = Article.objects.create(
            title="Bản nháp Wi-Fi",
            content="VPN chưa xuất bản.",
            is_published=False,
        )

    def setUp(self):
        self.list_url = reverse("kb_api:article_list")
        self.detail_url = reverse(
            "kb_api:article_detail", args=[self.published.pk]
        )
        self.client.force_login(self.user)

    def test_anonymous_requests_return_json_401(self):
        self.client.logout()
        for url in (self.list_url, self.detail_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.json()["error"], "authentication_required")
                self.assertNotIn("Location", response.headers)
                self.assertIn("no-store", response.headers["Cache-Control"])

    def test_views_still_require_login_without_global_login_middleware(self):
        middleware = [
            item for item in settings.MIDDLEWARE
            if item != "accounts.middleware.LoginRequiredMiddleware"
        ]
        self.client.logout()
        with override_settings(MIDDLEWARE=middleware):
            client = Client()
            for url in (self.list_url, self.detail_url):
                with self.subTest(url=url):
                    response = client.get(url)
                    self.assertEqual(response.status_code, 401)
                    self.assertEqual(
                        response.json()["error"], "authentication_required"
                    )

    def test_list_contains_only_published_articles(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertIn("no-store", response.headers["Cache-Control"])
        data = response.json()
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["page_size"], 6)
        self.assertEqual(
            [item["id"] for item in data["results"]],
            [self.content_match.pk, self.published.pk],
        )
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])

    def test_search_matches_title_or_content_and_hides_drafts(self):
        for query, article in (("  wi-fi  ", self.published), ("vpn", self.content_match)):
            with self.subTest(query=query):
                response = self.client.get(self.list_url, {"q": query})
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["query"], query.strip())
                self.assertEqual(data["count"], 1)
                self.assertEqual([item["id"] for item in data["results"]], [article.pk])

    def test_no_search_matches_returns_an_empty_page(self):
        response = self.client.get(self.list_url, {"q": "not-found-xyz"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["results"], [])
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["num_pages"], 1)
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])

    def test_published_detail_contains_the_article_fields(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            set(data), {"id", "title", "content", "created_at", "updated_at"}
        )
        self.assertEqual(data["id"], self.published.pk)
        self.assertEqual(data["title"], self.published.title)
        self.assertEqual(data["content"], self.published.content)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_draft_and_missing_detail_return_json_404(self):
        for pk in (self.draft.pk, self.draft.pk + 1000):
            with self.subTest(pk=pk):
                url = reverse("kb_api:article_detail", args=[pk])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json()["error"], "not_found")

    def test_pagination_links_preserve_search_and_order_is_stable(self):
        query = "Phân trang & VPN"
        ids = [
            Article.objects.create(
                title=f"{query} {number}", content="Bài kiểm thử.", is_published=True
            ).pk
            for number in range(7)
        ]
        Article.objects.filter(pk__in=ids).update(created_at=timezone.now())
        first = self.client.get(self.list_url, {"q": query}).json()
        self.assertEqual(first["count"], 7)
        self.assertEqual(first["num_pages"], 2)
        self.assertEqual(len(first["results"]), 6)
        self.assertEqual(parse_qs(urlsplit(first["next"]).query)["q"], [query])
        second = self.client.get(first["next"]).json()
        self.assertEqual(second["page"], 2)
        self.assertEqual(len(second["results"]), 1)
        self.assertIsNone(second["next"])
        self.assertEqual(
            [item["id"] for item in first["results"] + second["results"]],
            list(reversed(ids)),
        )
        self.assertEqual(self.client.get(second["previous"]).json(), first)

    def test_invalid_page_numbers_follow_the_existing_kb_behavior(self):
        for number in range(5):
            Article.objects.create(
                title=f"Extra {number}", content="Test.", is_published=True
            )
        for value, expected_page in (("abc", 1), ("0", 2), ("-1", 2), ("999", 2)):
            with self.subTest(page=value):
                response = self.client.get(self.list_url, {"page": value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["page"], expected_page)

    def test_write_methods_are_rejected_without_changing_articles(self):
        original_count = Article.objects.count()
        for url in (self.list_url, self.detail_url):
            for method in ("post", "put", "patch", "delete"):
                with self.subTest(url=url, method=method):
                    response = getattr(self.client, method)(url)
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response.json()["error"], "method_not_allowed")
                    self.assertEqual(response.headers["Allow"], "GET, HEAD")
        self.assertEqual(Article.objects.count(), original_count)

    def test_head_returns_no_body(self):
        for url in (self.list_url, self.detail_url):
            with self.subTest(url=url):
                response = self.client.head(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b"")

    def test_html_kb_still_redirects_anonymous_users_to_login(self):
        self.client.logout()
        target = reverse("kb:article_list") + "?q=wifi&page=2"
        response = self.client.get(target)
        self.assertEqual(response.status_code, 302)
        redirect = urlsplit(response.url)
        self.assertEqual(redirect.path, reverse("accounts:login"))
        self.assertEqual(parse_qs(redirect.query)["next"], [target])
