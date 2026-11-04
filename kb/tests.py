from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Article


class KnowledgeBaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="kb_test_user",
            password="TestPassword_KB_2026!",
        )

        cls.published = Article.objects.create(
            title="Huong dan Wi-Fi",
            content="Kiem tra ket noi mang.",
            is_published=True,
        )

        cls.content_match = Article.objects.create(
            title="Huong dan ket noi tu xa",
            content="Kiem tra cau hinh VPN.",
            is_published=True,
        )

        cls.draft = Article.objects.create(
            title="Ban nhap Wi-Fi",
            content="Noi dung VPN chua xuat ban.",
            is_published=False,
        )

    def setUp(self):
        self.list_url = reverse("kb:article_list")
        self.client.force_login(self.user)

    def detail_url(self, article):
        return reverse("kb:article_detail", args=[article.pk])

    def test_login_required_for_list_and_detail(self):
        self.client.logout()

        urls = [
            self.list_url,
            self.detail_url(self.published),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)

                redirect_url = urlsplit(response.url)
                self.assertEqual(
                    redirect_url.path,
                    reverse("accounts:login"),
                )
                self.assertEqual(
                    parse_qs(redirect_url.query).get("next"),
                    [url],
                )

    def test_list_shows_only_published_articles(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kb/article_list.html")

        articles = list(response.context["articles"])

        self.assertCountEqual(
            articles,
            [self.published, self.content_match],
        )
        self.assertNotContains(response, self.draft.title)

    def test_published_article_detail(self):
        response = self.client.get(self.detail_url(self.published))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kb/article_detail.html")
        self.assertEqual(
            response.context["article"],
            self.published,
        )
        self.assertContains(response, self.published.title)
        self.assertContains(response, self.published.content)

    def test_draft_and_missing_article_return_404(self):
        missing_pk = max(
            self.published.pk,
            self.content_match.pk,
            self.draft.pk,
        ) + 1

        urls = [
            self.detail_url(self.draft),
            reverse("kb:article_detail", args=[missing_pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)

    def test_search_title_and_content_excludes_drafts(self):
        cases = [
            ("  wi-fi  ", self.published),
            ("vpn", self.content_match),
        ]

        for query, expected_article in cases:
            with self.subTest(query=query):
                response = self.client.get(
                    self.list_url,
                    {"q": query},
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.context["query"],
                    query.strip(),
                )
                self.assertEqual(
                    list(response.context["articles"]),
                    [expected_article],
                )
                self.assertNotContains(response, self.draft.title)

    def test_search_with_no_results(self):
        response = self.client.get(
            self.list_url,
            {"q": "khong-co-bai-nao-xyz"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["page_obj"].paginator.count,
            0,
        )
        self.assertEqual(list(response.context["articles"]), [])

    def test_pagination_and_search_links(self):
        # Tao 7 bai cung tu khoa de kiem tra 2 trang.
        for number in range(7):
            Article.objects.create(
                title=f"Pagination sample {number}",
                content="Huong dan kiem thu phan trang.",
                is_published=True,
            )

        query = "Pagination"

        first_response = self.client.get(
            self.list_url,
            {"q": query, "page": 1},
        )
        self.assertEqual(first_response.status_code, 200)

        first_page = first_response.context["page_obj"]

        self.assertEqual(first_page.paginator.count, 7)
        self.assertEqual(first_page.paginator.num_pages, 2)
        self.assertEqual(len(first_page.object_list), 6)
        self.assertContains(
            first_response,
            "?q=Pagination&amp;page=2",
        )

        second_response = self.client.get(
            self.list_url,
            {"q": query, "page": 2},
        )
        self.assertEqual(second_response.status_code, 200)

        second_page = second_response.context["page_obj"]

        self.assertEqual(second_page.number, 2)
        self.assertEqual(len(second_page.object_list), 1)
        self.assertContains(
            second_response,
            "?q=Pagination&amp;page=1",
        )

        # Hai trang phai chua du 7 bai, dung thu tu, khong lap.
        actual_ids = [
            article.pk
            for article in (
                list(first_page.object_list)
                + list(second_page.object_list)
            )
        ]
        expected_ids = list(
            Article.objects.filter(
                is_published=True,
                title__icontains=query,
            )
            .order_by("-created_at", "-pk")
            .values_list("pk", flat=True)
        )

        self.assertEqual(actual_ids, expected_ids)