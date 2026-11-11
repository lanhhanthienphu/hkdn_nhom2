# Bàn giao tích hợp Backend 2 với BE1 và frontend

Đây là giao diện dịch vụ email đã có mã nguồn và các điểm tích hợp cần thống nhất khi BE1 hoàn thành Ticket.
Tên trường trong model Ticket do BE1 quyết định; các hàm dưới đây chỉ nhận dữ liệu chuỗi.

## Email

| event | Thời điểm BE1 gọi | Người nhận dự kiến |
| --- | --- | --- |
| created | Ticket thật được tạo và lưu thành công | Người gửi yêu cầu |
| assigned | Một kỹ thuật viên được phân công mới | Kỹ thuật viên được phân công |
| resolved | Ticket chuyển từ trạng thái khác sang đã giải quyết | Người gửi yêu cầu |

BE1 xác định người nhận từ dữ liệu người dùng và quyền nghiệp vụ trên server. Không lấy email người nhận tùy ý từ form tạo ticket.
Các thao tác save không đổi sự kiện/trạng thái không nên tự phát lại cùng thông báo.

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

Ví dụ khung tích hợp, chỉ dùng sau khi đã có luồng lưu Ticket thật:

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
preview_ticket_email chỉ dựng/xem nội dung, không dùng mailer để gửi; nó vẫn an toàn để xem trước khi môi trường đã cấu hình SMTP.
Kiểm thử dùng hộp thư bộ nhớ của Django; không tạo ticket thật hoặc gửi email ra bên ngoài.
Khi triển khai SMTP thực tế, nhóm cung cấp host/port/tài khoản/secret bằng biến môi trường và thay MAILERS theo tài liệu Django 6.1. Không đặt mật khẩu vào repository.

## Tệp đính kèm

Bộ kiểm tra tickets.attachment_validators.validate_attachment và tài liệu BACKEND2_ATTACHMENTS.md đã có.
BE1/BE2 cần thống nhất các điểm sau trước khi lưu và tải tệp thật:

| Điểm tích hợp | Cần thống nhất |
| --- | --- |
| Liên kết dữ liệu | Tệp thuộc ticket nào, người tải lên, tên hiển thị và đường dẫn lưu |
| Tạo ticket | Thời điểm lưu nội dung tệp; cách dọn tệp nếu giao dịch ticket thất bại |
| Quyền tải | Người tạo ticket, người được phân công và vai trò quản trị được phép nào |
| URL tải | Endpoint có kiểm tra quyền theo ticket; phản hồi cho người không có quyền |
| Lưu trữ | Vị trí media riêng, tên tệp tránh va chạm và chính sách xóa khi xóa ticket |

Giữ bộ kiểm tra dung lượng/nội dung hiện có trong đường đi ghi tệp của backend thật.
Hiện demo_store chỉ ghi metadata tên và dung lượng; việc vượt qua validator không có nghĩa nội dung đã được lưu.

## Frontend

API KB đọc đã có tại /api/kb/articles/ và /api/kb/articles/<id>/.
Dùng BACKEND2_KB_API.md làm hợp đồng dữ liệu, đăng nhập session, 401, 404 và phân trang.
Đường dẫn ticket trong email phải trỏ tới trang chi tiết thực tế mà nhóm thống nhất; không mặc định rằng đường dẫn demo Django và React có cùng cách xác thực.

## Nghiệm thu độc lập

- Test notifications kiểm tra nội dung, người nhận, escape HTML, lỗi dữ liệu, thời điểm commit/rollback, lỗi backend và xem trước.
- Test KB mẫu kiểm tra dry-run, chạy lặp không trùng, xuất bản/phân trang API và giữ nguyên bài đã có.
- Test KB, accounts và ticket demo hiện có tiếp tục chạy cùng bộ.
- CI cần có lần chạy thực tế thành công sau khi push.
