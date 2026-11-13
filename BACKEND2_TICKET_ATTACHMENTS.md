# Backend 2 — Lưu và tải tệp đính kèm Ticket

Bản cập nhật dành cho code BE1 tại commit `0cdf50485d71d68eb63c01b25218b895cff8c23e`.
Người thực hiện tiếp tục làm trên `backend/lam`, có thể commit từng phần trên máy rồi push chung một lần khi hoàn tất.

## Kết quả

- Model `Attachment` liên kết `Ticket`, ghi người tải lên, tên gốc, dung lượng thực tế và ngày tải.
- Khi tạo ticket thật, form vẫn cho chọn một tệp JPG/JPEG/PNG/PDF/TXT/LOG, tối đa 10 MiB.
- Sử dụng lại bộ kiểm tra nội dung hiện có. Không tin MIME do trình duyệt khai báo.
- Lưu byte vào `private_uploads/tickets/<id>/<UUID>.<đuôi>`; hai tệp cùng tên không ghi đè nhau.
- Trang chi tiết có liên kết **Tải tệp**. Tệp vẫn tải được khi người tạo đăng xuất và đăng nhập lại.
- URL tải yêu cầu đăng nhập và dùng quyền `Ticket.can_view()` của BE1. Một tài khoản thông thường khác nhận 404.
- Django Admin có mục tệp đính kèm chỉ đọc trong Ticket; liên kết tải dùng cùng kiểm tra quyền.
- Khi lưu database thất bại sau khi file đã được ghi, dịch vụ cố gắng dọn file và rollback các bản ghi mới.
- Xóa bản ghi Attachment hoặc xóa Ticket sẽ đăng ký xóa file sau commit; rollback việc xóa sẽ giữ file.
- Giữ nguyên ticket/bình luận cũ. Ticket chỉ có tên/dung lượng file tiếp tục hiển thị thông tin đó, không có liên kết tải giả.
- Chế độ demo hiện có vẫn chỉ lưu metadata. Các nhãn "xem thử" trên trang tạo/chi tiết chỉ hiện trong chế độ demo.

## Áp dụng trên Windows

Đặt `backend2-ticket-attachments.patch` cạnh `manage.py`. Nếu server đang chạy, nhấn Ctrl+C.

```powershell
git status
git branch --show-current
Test-Path .\backend2-ticket-attachments.patch
git apply --check backend2-ticket-attachments.patch
```

Nhánh cần dùng là `backend/lam`; commit gốc là `0cdf504` hoặc một phiên bản tương thích.
Nếu kiểm tra patch báo lỗi, giữ lại thông báo và đối chiếu thay đổi cục bộ trước khi áp dụng; không chép đè file bằng tay.
Các file patch cũ chưa được theo dõi có thể giữ nguyên.

Khi `git apply --check` không báo lỗi:

```powershell
git apply backend2-ticket-attachments.patch
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test kb accounts tickets notifications
```

Migration mới là `tickets/0003_attachment.py`; đã kèm sẵn, không cần tự tạo migration.
Không bổ sung thư viện Python. Bộ requirements đang dùng để chạy 100 test trước đó vẫn đủ.

## Kiểm tra bằng trình duyệt

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

1. Đăng nhập bằng tài khoản người dùng thường A.
2. Mở `http://127.0.0.1:8000/tickets/new/`, điền thông tin và chọn một file TXT/LOG UTF-8 hoặc ảnh PNG/JPG hợp lệ.
3. Tạo ticket. Trang chi tiết hiển thị tên file, dung lượng và liên kết **Tải tệp**.
4. Tải lại và so sánh nội dung với file ban đầu.
5. Đăng xuất rồi đăng nhập lại cùng tài khoản; mở ticket và tải lại file.
6. Sao chép URL của liên kết tải. Mở cửa sổ riêng tư, đăng nhập tài khoản thường B và mở URL đó: kết quả phải là 404.
7. Kỹ thuật viên/quản trị theo vai trò và superuser được xem/tải theo quy tắc của BE1. Vì vậy không dùng tài khoản quản trị để thử tình huống người không có quyền.
8. Thử file sai định dạng hoặc vượt 10 MiB: có lỗi tại form, không tạo ticket/file mới.
9. Mở một ticket cũ chỉ có tên file: vẫn đọc được thông tin, không xuất hiện nút tải cho file chưa từng được lưu.

Thiết lập mặc định của commit gốc không khai báo `FRONTEND_DEMO_ENABLED` và chạy luồng database thật.
Giữ nguyên thiết lập đó. Trong code BE1 hiện tại, `True` là demo và `False` vô hiệu hóa các trang demo; không đặt `False` để chuyển sang database thật.

## Hợp đồng tích hợp

Model:

```python
from tickets.models import Attachment

# ticket.attachments.all() trả về các bản ghi file của ticket.
```

Dịch vụ tạo ticket dùng dữ liệu đã qua `TicketForm.is_valid()`:

```python
from tickets.attachment_services import create_ticket_with_attachment

ticket = create_ticket_with_attachment(author=request.user, data=form.cleaned_data)
```

- Người tạo được lấy từ phiên đăng nhập, không lấy từ trường form do trình duyệt gửi.
- Dịch vụ kiểm tra lại file trước khi ghi byte và dùng `transaction.atomic(durable=True)`.
- Dịch vụ phải sở hữu giao dịch ngoài cùng. View tạo ticket đã dùng `non_atomic_requests` để tránh một giao dịch yêu cầu HTTP bọc bên ngoài.
- Không bọc lời gọi dịch vụ trong một `atomic()` khác. Điều này ngăn việc database rollback ở bên ngoài sau khi dịch vụ đã cho rằng file được lưu thành công.
- Bản cập nhật email tiếp theo đã đăng ký `notify_ticket_event(ticket, 'created')` trong giao dịch của dịch vụ. Không đăng ký lại ở view; xem [BACKEND2_TICKET_EMAIL.md](BACKEND2_TICKET_EMAIL.md).

Tải tệp:

```text
GET hoặc HEAD /tickets/<ticket_id>/attachments/<attachment_id>/download/
Tên route: tickets:attachment_download
```

| Tình huống | Kết quả |
| --- | --- |
| Chưa đăng nhập | Chuyển đến trang đăng nhập |
| Có quyền xem Ticket và file tồn tại | Trả file bằng FileResponse |
| Không có quyền, sai ID, ID file thuộc ticket khác hoặc mất nội dung file | 404 |
| Phương thức khác GET/HEAD khi đã đăng nhập | 405 |

Phản hồi tải dùng `Content-Disposition: attachment`, `application/octet-stream`, `nosniff` và `Cache-Control: private, no-store`.
Tên file tải về vẫn là tên gốc đã bỏ thành phần đường dẫn/ký tự điều khiển. Tên lưu trên máy chủ do hệ thống tạo.

## Vận hành và giới hạn

- `PRIVATE_ATTACHMENT_ROOT` mặc định là thư mục `private_uploads` cạnh `manage.py`, đã được loại khỏi Git.
- Không tạo route `static(..., document_root=PRIVATE_ATTACHMENT_ROOT)` và không cấu hình web server công khai thư mục này.
- Khi triển khai, tiến trình Django cần quyền đọc/ghi thư mục và nhóm cần sao lưu cả database lẫn thư mục file.
- File đã tải lên và database trên máy bạn không được chuyển cho người khác chỉ bằng `git push`.
- Hiện chỉ nhận một file lúc tạo Ticket. Model hỗ trợ liên kết nhiều bản ghi nhưng chưa có luồng thêm/thay thế/xóa từng file trên trang chi tiết.
- File gắn với ticket cũ chỉ có metadata không thể khôi phục nội dung từ tên/dung lượng.
- Database và filesystem không có giao dịch chung: mất điện/ngắt tiến trình giữa lúc ghi, lỗi ghi một phần hoặc lỗi dọn file vẫn có thể để lại file dư. Lỗi dọn file đã lưu được ghi log; khi vận hành cần đối chiếu bản ghi và file trước khi dọn.
- Bộ kiểm tra định dạng không thay thế chương trình quét mã độc.

## Kiểm thử đã chạy khi đóng gói

- Python 3.13.5, Django 6.1.2, SQLite, Pillow 13.0.0, pypdf 6.21.4.
- 30 test mới tại `tickets/test_attachments.py` kiểm tra lưu/tải byte thật, file ảnh, phiên đăng nhập mới, quyền truy cập, tên trùng, file cũ, rollback và xóa sau commit.
- Toàn bộ `test kb accounts tickets notifications`: **130/130 PASS** trong môi trường chuẩn bị bản vá.
- Các test dùng thư mục tạm và database test; không dùng database/file thật của người dùng.
- Kết quả GitHub Actions trên nhánh của bạn chỉ có sau khi push bản cập nhật.

## Lưu commit và push khi hoàn tất

Sau khi test và thử giao diện thành công, dừng server rồi xem thay đổi:

```powershell
git diff --check
git diff --stat
git status
```

Chọn các file của bản cập nhật:

```powershell
git add .gitignore helpdesk_system/settings.py BACKEND2_ATTACHMENTS.md BACKEND2_INTEGRATION.md BACKEND2_TICKET_ATTACHMENTS.md
git add tickets/admin.py tickets/apps.py tickets/forms.py tickets/models.py tickets/views.py tickets/urls.py
git add tickets/attachment_services.py tickets/attachment_signals.py tickets/attachment_storage.py tickets/attachment_validators.py tickets/test_attachments.py tickets/migrations/0003_attachment.py
git add templates/tickets/_attachments.html templates/tickets/create.html templates/tickets/detail.html
git diff --cached --stat
git commit -m "feat: store and download ticket attachments with access checks"
```

Commit chỉ lưu trên máy. Có thể tiếp tục làm phần email và tạo commit riêng; sau khi hoàn tất những phần muốn gộp, chỉ cần push một lần:

```powershell
git push origin backend/lam
```

Không cần đưa file `.patch`, `db.sqlite3` hoặc `private_uploads` vào commit.

## Tài liệu chính thức

- FileResponse: https://docs.djangoproject.com/en/6.1/ref/request-response/#fileresponse-objects
- Giao dịch và on_commit: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- File storage: https://docs.djangoproject.com/en/6.1/ref/files/storage/
