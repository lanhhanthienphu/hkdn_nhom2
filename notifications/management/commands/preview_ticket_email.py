from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from notifications.services import EVENTS, build_ticket_email


class Command(BaseCommand):
    help = "Xem trước email bằng dữ liệu mẫu; không gửi thư."

    def add_arguments(self, parser):
        parser.add_argument("event", choices=EVENTS)
        parser.add_argument(
            "--html-output",
            help="Lưu bản HTML UTF-8 vào đường dẫn này để mở bằng trình duyệt.",
        )

    def handle(self, *args, **options):
        message = build_ticket_email(
            event=options["event"],
            ticket_code="HD-DEMO-001",
            title="Không kết nối được Wi-Fi tại phòng A.201",
            to_email="demo@example.test",
            ticket_url="http://127.0.0.1:8000/tickets/1001/",
            recipient_name="Người dùng mẫu",
            assignee_name="Kỹ thuật viên mẫu",
        )
        self.stdout.write("XEM TRƯỚC EMAIL — DỮ LIỆU MẪU")
        self.stdout.write(f"Người nhận: {message.to[0]}")
        self.stdout.write(f"Tiêu đề: {message.subject}")
        self.stdout.write("")
        self.stdout.write(message.body)

        if options["html_output"]:
            target = Path(options["html_output"]).expanduser()
            try:
                target.write_text(message.alternatives[0].content, encoding="utf-8")
            except OSError as error:
                raise CommandError(f"Không lưu được HTML: {error}") from error
            self.stdout.write(self.style.SUCCESS(f"Đã lưu HTML: {target.resolve()}"))

        self.stdout.write("Bản xem trước không gửi email và không tạo ticket.")
