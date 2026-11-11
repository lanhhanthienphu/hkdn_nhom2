from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Article


class KnowledgeBaseDemoContentTests(TestCase):
    def test_dry_run_does_not_write_articles(self):
        output = StringIO()
        call_command("seed_kb_demo", dry_run=True, stdout=output)
        self.assertIn("sẽ tạo 7 bài", output.getvalue())
        self.assertEqual(Article.objects.count(), 0)

    def test_default_creates_drafts_and_reruns_do_not_duplicate(self):
        call_command("seed_kb_demo", stdout=StringIO())
        self.assertEqual(Article.objects.count(), 7)
        self.assertFalse(Article.objects.filter(is_published=True).exists())
        before = list(Article.objects.values_list("pk", "updated_at"))
        call_command("seed_kb_demo", stdout=StringIO())
        self.assertEqual(list(Article.objects.values_list("pk", "updated_at")), before)

    def test_publish_produces_two_api_pages(self):
        call_command("seed_kb_demo", publish=True, stdout=StringIO())
        user = get_user_model().objects.create_user(username="seed_kb_reader")
        self.client.force_login(user)
        url = reverse("kb_api:article_list")
        first = self.client.get(url, {"q": "[Mẫu]"}).json()
        self.assertEqual(first["count"], 7)
        self.assertEqual(len(first["results"]), 6)
        second = self.client.get(first["next"]).json()
        self.assertEqual(len(second["results"]), 1)

    def test_existing_article_is_never_overwritten_or_republished(self):
        existing = Article.objects.create(
            title="[Mẫu] Kiểm tra khi máy tính không kết nối được Wi-Fi",
            content="Nội dung đã được người dùng chỉnh sửa.",
            is_published=False,
        )
        old_updated_at = existing.updated_at
        call_command("seed_kb_demo", publish=True, stdout=StringIO())
        existing.refresh_from_db()
        self.assertEqual(Article.objects.count(), 7)
        self.assertEqual(existing.content, "Nội dung đã được người dùng chỉnh sửa.")
        self.assertFalse(existing.is_published)
        self.assertEqual(existing.updated_at, old_updated_at)
