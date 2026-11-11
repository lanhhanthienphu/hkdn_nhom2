from django.core.management.base import BaseCommand
from django.db import transaction

from kb.demo_content import DEMO_ARTICLES
from kb.models import Article


class Command(BaseCommand):
    help = "Tạo 7 bài KB mẫu, bỏ qua bài đã có cùng tiêu đề."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Xem trước, không ghi dữ liệu.")
        parser.add_argument("--publish", action="store_true", help="Xuất bản các bài được tạo mới.")

    def handle(self, *args, **options):
        created = skipped = 0
        with transaction.atomic():
            for data in DEMO_ARTICLES:
                if Article.objects.filter(title=data["title"]).exists():
                    skipped += 1
                    self.stdout.write(f"Đã có, giữ nguyên: {data['title']}")
                    continue

                created += 1
                if options["dry_run"]:
                    self.stdout.write(f"Sẽ tạo: {data['title']}")
                else:
                    Article.objects.create(
                        **data,
                        is_published=options["publish"],
                    )

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(
                f"Xem trước: sẽ tạo {created} bài; giữ nguyên {skipped} bài đã có."
            ))
        else:
            state = "đã xuất bản" if options["publish"] else "bản nháp"
            self.stdout.write(self.style.SUCCESS(
                f"Đã tạo {created} bài {state}; giữ nguyên {skipped} bài đã có."
            ))
