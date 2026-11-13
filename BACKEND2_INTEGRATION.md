# Bàn giao tích hợp Backend 2 với BE1 và frontend

Ticket của BE1 đã có tại `tickets.models.Ticket`. Phần lưu/tải tệp thật đã được nối vào luồng tạo Ticket.
Dịch vụ email đã nối vào tạo Ticket thật, phân công và chuyển sang trạng thái đã xử lý, kể cả thao tác qua Django Admin.
Hướng dẫn áp dụng và kiểm tra: [BACKEND2_TICKET_EMAIL.md](BACKEND2_TICKET_EMAIL.md).

## Email

| event | Thời điểm gọi | Người nhận |
| --- | --- | --- |
| created | Ticket thật được tạo và lưu thành công | Người gửi yêu cầu |
| assigned | Một kỹ thuật viên được phân công mới | Kỹ thuật viên được phân công |
| resolved | Ticket chuyển từ trạng thái khác sang đã giải quyết | Người gửi yêu cầu |

`notifications.ticket_events.notify_ticket_event(ticket, event)` xác định người nhận từ tài khoản trong database.
Không lấy email hay URL người nhận từ form hoặc Host của request. Thiếu email hoặc cấu hình không hợp lệ sẽ bỏ qua thông báo và ghi log; Ticket vẫn lưu được.
`HELPDESK_BASE_URL` là địa chỉ gốc dùng dựng URL chi tiết Ticket, mặc định `http://127.0.0.1:8000`.

- `create_ticket_with_attachment()` đã đăng ký thông báo `created` trong giao dịch tạo Ticket.
- `Ticket.assign_technician()` và `Ticket.change_status()` ghi thay đổi, lịch sử và đăng ký email trong cùng giao dịch.
- `TicketAdmin.save_model()` xử lý những sự kiện tương ứng khi quản trị viên lưu form.
- Lưu lại cùng người được phân công hoặc cùng trạng thái không tạo thêm lịch sử/email. Mở lại rồi giải quyết là một sự kiện mới.
- `Ticket.objects.create()`, `save()` và `QuerySet.update()` gọi trực tiếp không tự gửi email. API hoặc command mới cần dùng dịch vụ/phương thức nghiệp vụ thích hợp và kiểm tra quyền người gọi.
- Không gọi thêm hàm gửi email sau các điểm tích hợp trên vì sẽ gửi trùng.

Giao diện hàm:

```python
from notifications.services import (
    build_ticket_email,
    send_ticket_notification,
    notify_ticket_after_commit,
)

payload = {
    "event": "created",
    "ticket_code": "HD-2026-001",
    "title": "Không kết nối được Wi-Fi",
    "to_email": "student@example.test",
    "ticket_url": "https://helpdesk.example.test/tickets/1/",
    "recipient_name": "Trường Lâm",
    "assignee_name": "",
    "status_label": "Chờ tiếp nhận",
}

# Chỉ dựng nội dung; chưa gửi.
message = build_ticket_email(**payload)

# Gửi trực tiếp qua MAILERS hiện được cấu hình.
# sent_count = send_ticket_notification(**payload)

# Trong luồng ghi Ticket, đăng ký thông báo sau commit:
# notify_ticket_after_commit(**payload)
```

event, ticket_code, title, to_email và ticket_url là bắt buộc.
recipient_name, assignee_name và status_label là tùy chọn. Trạng thái không được suy ra từ tên sự kiện; BE1 truyền nhãn thực tế nếu cần hiển thị.
ticket_url phải là URL HTTP/HTTPS tuyệt đối đến hệ thống do server dựng. URL trong ví dụ là minh họa.
Thiếu trường bắt buộc, email sai hoặc URL không hợp lệ sẽ phát sinh django.core.exceptions.ValidationError trước khi gửi.
Tiêu đề và mã ticket được chuẩn hóa xuống một dòng để không tạo thêm header.

### Ranh giới giao dịch và lỗi

Ví dụ cho một luồng nghiệp vụ mới; các điểm tích hợp đã liệt kê ở trên đã thực hiện việc này:

```python
from django.db import transaction
from notifications.services import notify_ticket_after_commit

with transaction.atomic():
    # BE1 lưu ticket/phân công/trạng thái tại đây.
    # Dựng payload từ bản ghi và người nhận đã được kiểm tra quyền.
    notify_ticket_after_commit(**payload)
```

Thông báo chỉ được gửi sau commit thành công; rollback sẽ bỏ callback.
Ngoài một giao dịch đang mở, Django thực thi callback ngay.
robust=True ghi lỗi gửi vào log của Django để lỗi gửi không ngăn các callback tiếp theo.
Hàm gửi trực tiếp báo lỗi backend cho bên gọi; nó không cố tình nuốt lỗi SMTP.
Callback chạy đồng bộ sau commit; chưa có hàng đợi, gửi lại tự động, nhật ký giao nhận hoặc chống trùng dựa trên event_id. Nếu cần các chức năng đó, thống nhất cách lưu sự kiện với BE1 trước.

### Môi trường phát triển

MAILERS mặc định của dự án đang là console.EmailBackend: lệnh gửi chỉ in nội dung ở terminal.
DEFAULT_FROM_EMAIL đọc biến môi trường HELPDESK_FROM_EMAIL, mặc định helpdesk@example.test.
HELPDESK_BASE_URL đọc biến môi trường cùng tên; chỉ gồm HTTP/HTTPS, tên miền/IP và cổng nếu có, không có đường dẫn/query/fragment.
preview_ticket_email chỉ dựng/xem nội dung, không dùng mailer để gửi; nó vẫn an toàn để xem trước khi môi trường đã cấu hình SMTP.
Kiểm thử dùng hộp thư bộ nhớ của Django; không tạo ticket thật hoặc gửi email ra bên ngoài.
Khi triển khai SMTP thực tế, nhóm cung cấp host/port/tài khoản/secret bằng biến môi trường và thay MAILERS theo tài liệu Django 6.1. Không đặt mật khẩu vào repository.

## Tệp đính kèm

Đã triển khai lưu/tải tệp; hướng dẫn chi tiết tại [BACKEND2_TICKET_ATTACHMENTS.md](BACKEND2_TICKET_ATTACHMENTS.md).

| Điểm tích hợp | Đã triển khai |
| --- | --- |
| Liên kết dữ liệu | `Attachment.ticket`, `uploaded_by`, `original_name`, `size`, `file`, `created_at` |
| Tạo ticket | `create_ticket_with_attachment(author=..., data=...)` sở hữu giao dịch ngoài cùng, dọn tệp đã lưu nếu thao tác thất bại |
| Quyền tải | Dùng nguyên `Ticket.can_view()`: chủ ticket, người được gán, kỹ thuật viên/quản trị theo vai trò và superuser |
| URL tải | `GET/HEAD /tickets/<ticket_id>/attachments/<attachment_id>/download/`; đăng nhập trước, sai quyền/ID trả 404 |
| Lưu trữ | `PRIVATE_ATTACHMENT_ROOT`, tên UUID, không có URL media công khai; xóa tệp sau khi việc xóa bản ghi đã commit |

Bộ kiểm tra `validate_attachment()` chạy ở form và trước khi lưu file thật.
`demo_store` vẫn chỉ ghi metadata; các ticket cũ chỉ có tên/dung lượng không được tạo file giả.
Luồng hiện tại nhận một tệp lúc tạo ticket; chưa có thao tác thêm, thay thế hoặc xóa từng tệp từ trang chi tiết.
Email đã được đăng ký bên trong giao dịch của dịch vụ tạo ticket; không bọc dịch vụ này trong một `atomic()` khác và không đăng ký email lần thứ hai ở view.

## Frontend

API KB đọc đã có tại /api/kb/articles/ và /api/kb/articles/<id>/.
Dùng BACKEND2_KB_API.md làm hợp đồng dữ liệu, đăng nhập session, 401, 404 và phân trang.
Đường dẫn ticket trong email phải trỏ tới trang chi tiết thực tế mà nhóm thống nhất; không mặc định rằng đường dẫn demo Django và React có cùng cách xác thực.

## Nghiệm thu độc lập

- Test notifications kiểm tra nội dung, người nhận, escape HTML, lỗi dữ liệu, thời điểm commit/rollback, lỗi backend và xem trước.
- `tickets/test_notifications.py` kiểm tra tích hợp thật qua view, model, Admin, chống gửi lặp khi lưu không đổi, rollback và lỗi SMTP sau commit thật.
- Test KB mẫu kiểm tra dry-run, chạy lặp không trùng, xuất bản/phân trang API và giữ nguyên bài đã có.
- Test KB, accounts và ticket demo hiện có tiếp tục chạy cùng bộ.
- CI cần có lần chạy thực tế thành công sau khi push.
