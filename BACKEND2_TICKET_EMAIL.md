# Email cho các sự kiện Ticket thật

Bản vá `backend2-ticket-email.patch` áp dụng sau `backend2-ticket-attachments.patch` trên nền BE1 `0cdf504`.
Tiếp tục làm trên nhánh `backend/lam`; không cần push trước khi áp dụng. Bản vá này không thêm migration hoặc thư viện mới.

## Những gì thay đổi

| Thao tác | Người nhận | Khi nào gửi |
| --- | --- | --- |
| Tạo Ticket qua trang tạo ticket hoặc Admin | Người tạo ticket | Sau khi lưu thành công |
| Phân công kỹ thuật viên qua endpoint BE1 hoặc Admin | Người được phân công mới | Sau khi lưu thay đổi người phụ trách |
| Chuyển trạng thái sang `resolved` / Đã xử lý | Người tạo ticket | Sau khi lưu chuyển trạng thái |

Lưu lại cùng người phụ trách hoặc cùng trạng thái không phát thêm email. Chuyển sang trạng thái khác rồi giải quyết lại là một sự kiện mới.
Tạo ticket trong Admin kèm người phụ trách gửi cả thông báo tiếp nhận và phân công. Tạo mới ngay ở trạng thái đã xử lý chỉ gửi tiếp nhận (và phân công nếu có), vì không có lần chuyển trạng thái trước đó.

Email lấy địa chỉ từ tài khoản trong database, đường dẫn từ cấu hình máy chủ. Không gửi nội dung file đính kèm trong email; người nhận mở trang ticket và phải có quyền xem/tải tệp.
Phiên xem thử `demo_store` không gửi email thật. Phản hồi và sửa tiêu đề cũng không phát lại ba sự kiện trên.

## Áp dụng trên Windows

Đặt file patch cạnh `manage.py`. Trong terminal đang ở thư mục dự án:

```powershell
git status
git apply --check .\backend2-ticket-email.patch
```

Lệnh kiểm tra thành công thường không in gì. Sau đó:

```powershell
git apply .\backend2-ticket-email.patch
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test kb accounts tickets notifications
```

Nếu `git apply --check` báo lỗi, dừng tại đó và giữ lại thông báo; không dùng `--reject` hoặc chép đè file đang sửa.
Không cần áp dụng lại bản tệp đính kèm đã chạy đúng. Nếu có test lỗi, xử lý lỗi trước khi commit.

## Kiểm tra trực tiếp trên trình duyệt

1. Chạy `.\.venv\Scripts\python.exe manage.py runserver` và giữ terminal đó mở.
2. Đăng nhập tài khoản superuser tại `http://127.0.0.1:8000/admin/`. Trong phần tài khoản, nhập email hợp lệ cho người tạo ticket và cho tài khoản kỹ thuật viên dùng để thử. Bật trạng thái hoạt động của hai tài khoản.
3. Trong hồ sơ người dùng (`UserProfile`), gán vai trò `technician` cho tài khoản kỹ thuật viên. `is_staff` chỉ liên quan quyền vào Admin, không thay thế vai trò kỹ thuật viên của dự án. Có thể dùng superuser để thao tác phân công; tài khoản nhận phân công không cần quyền vào Admin.
4. Mở `http://127.0.0.1:8000/tickets/new/`, tạo ticket bằng tài khoản có email. Sau khi tạo thành công, terminal hiển thị email gửi tới email của người tạo, với mã `HD-<id>` và đường dẫn chi tiết.
5. Quay lại Admin bằng superuser, mở Ticket vừa tạo, chọn **Người phụ trách** là kỹ thuật viên rồi lưu. Email phân công hiển thị ở terminal, người nhận là kỹ thuật viên. Ticket mới được tự chuyển sang **Đang xử lý** nếu không chọn một trạng thái khác.
6. Mở lại Ticket, chọn trạng thái **Đã xử lý** rồi lưu. Email thông báo giải quyết hiển thị, người nhận là người tạo ticket.
7. Bấm lưu lần nữa mà không đổi người phụ trách/trạng thái: không xuất hiện thêm email.
8. Mở đường dẫn trong email khi đăng nhập tài khoản người nhận; kiểm tra đọc ticket và tải lại tệp của bước trước.

Dự án hiện dùng `console.EmailBackend`: email chỉ in ra terminal, chưa xuất hiện trong Gmail/Outlook.
Địa chỉ email hợp lệ là điều kiện để có thông báo. Nếu tài khoản không có email, ticket vẫn lưu bình thường và thông báo được bỏ qua.

## Cấu hình URL và mailer

Mặc định, email dẫn về `http://127.0.0.1:8000/tickets/<id>/`. Nếu chạy ở địa chỉ khác, đặt biến trước khi khởi động lại server:

```powershell
$env:HELPDESK_BASE_URL = "http://127.0.0.1:8000"
.\.venv\Scripts\python.exe manage.py runserver
```

Khi triển khai thật, thay bằng địa chỉ HTTPS của hệ thống. Giá trị chỉ chứa giao thức, host và cổng nếu có; không chứa `/tickets/`, tài khoản/mật khẩu, query hoặc fragment.
`HELPDESK_FROM_EMAIL` vẫn cấu hình địa chỉ gửi. Bản vá giữ nguyên mailer console; SMTP cần cấu hình riêng khi nhóm sẵn sàng gửi thật.
Lệnh xem mẫu có sẵn vẫn hoạt động và không gửi email: `python manage.py preview_ticket_email created`.

## Hợp đồng để BE1 tiếp tục tích hợp

- Tạo ticket: dùng `create_ticket_with_attachment(author=request.user, data=form.cleaned_data)` sau khi form hợp lệ. Hàm này đã gửi thông báo sau commit; không gọi hàm gửi thêm ở view.
- Phân công: `ticket.assign_technician(tech, by=request.user, note=...)`.
- Trạng thái: `ticket.change_status('resolved', by=request.user, note=...)`.
- Hai phương thức cập nhật trả `True` khi có thay đổi, `False` khi giá trị đã giống dữ liệu hiện tại. Chúng đọc lại bản ghi trong giao dịch trước khi so sánh, không chỉ dựa vào instance có thể đã cũ.
- Người nhận phân công mới phải đang hoạt động và có vai trò kỹ thuật viên/quản trị hoặc là superuser. Endpoint trả thông báo lỗi nếu chọn tài khoản không phù hợp; ID sai trả 404.
- Endpoint BE1 vẫn kiểm tra quyền người gọi. Các phương thức model không thay thế kiểm tra quyền ở view/API mới.
- Admin có form kiểm tra người phụ trách và hook lưu để ghi lịch sử/email, vì Admin không gọi hai phương thức nghiệp vụ trên.
- `save()`, `objects.create()` và cập nhật hàng loạt trực tiếp không tự gửi thông báo. Không thêm signal gửi email chung, tránh phát trùng với những điểm tích hợp đã có.

## Lỗi và giới hạn

- Ticket, lịch sử và đăng ký thông báo nằm trong cùng giao dịch database. Nếu giao dịch rollback, callback gửi email bị hủy.
- Gửi chỉ chạy sau commit. Lỗi backend gửi email được Django ghi log; ticket đã lưu và file đính kèm vẫn còn, các callback tiếp theo vẫn có thể chạy.
- Email/URL cấu hình không hợp lệ được ghi cảnh báo và bỏ qua, không làm mất ticket hợp lệ. Tài khoản không hoạt động hoặc thiếu email được bỏ qua ở mức log INFO.
- Callback gửi chạy đồng bộ sau commit; chưa có hàng đợi, tự gửi lại, nhật ký giao nhận hoặc bảo đảm giao email đúng một lần khi tiến trình gặp sự cố.
- Đọc trạng thái mới trong giao dịch ngăn gửi lặp do lưu lại tuần tự hoặc dùng instance cũ. `select_for_update()` chỉ khóa dòng trên database có hỗ trợ; SQLite không có khóa dòng như PostgreSQL/MySQL. Chưa kiểm thử tải đồng thời đa tiến trình hoặc triển khai SMTP thật.
- Chưa phát email khi bình luận, đóng ticket, bỏ phân công hoặc thay đổi nội dung khác. Chưa bổ sung nút phân công/trạng thái lên frontend; có thể thử đầy đủ qua Admin và endpoint BE1 đã có.

## Kiểm thử và bằng chứng

- `tickets/test_notifications.py`: 34 test mới qua POST tạo/phân công/đổi trạng thái, thao tác Admin thật, người nhận, URL tin cậy, lưu lặp, tài khoản không hợp lệ, demo, rollback và lỗi SMTP sau commit thật.
- Bộ test tổng: `python manage.py test kb accounts tickets notifications`.
- Đã kiểm tra trên snapshot BE1 cộng hai bản vá tệp/email: **164 tests — OK**, Django 6.1.2 / Python 3.13 / SQLite. Máy người dùng cần chạy lại lệnh test sau khi áp dụng.
- Kiểm tra migration: `python manage.py makemigrations --check --dry-run`.
- Khi báo cáo, chụp kết quả test `OK`, email trong terminal với đúng mã ticket và trang Admin sau khi phân công/đổi trạng thái. Ẩn địa chỉ email cá nhân trước khi chia sẻ rộng rãi.

## Commit rồi push chung khi đã kiểm tra xong

Nếu phần tệp và email đều chưa commit, có thể lưu chung các file đã sửa:

```powershell
git add .gitignore helpdesk_system/settings.py BACKEND2_ATTACHMENTS.md BACKEND2_INTEGRATION.md BACKEND2_TICKET_ATTACHMENTS.md BACKEND2_TICKET_EMAIL.md
git add tickets/admin.py tickets/apps.py tickets/forms.py tickets/models.py tickets/views.py tickets/urls.py
git add tickets/attachment_services.py tickets/attachment_signals.py tickets/attachment_storage.py tickets/attachment_validators.py tickets/test_attachments.py tickets/migrations/0003_attachment.py
git add templates/tickets/_attachments.html templates/tickets/create.html templates/tickets/detail.html
git add notifications/ticket_events.py tickets/test_notifications.py
git diff --cached --stat
git commit -m "feat: integrate ticket attachments and lifecycle notifications"
```

Nếu đã commit phần tệp, các file không thay đổi sẽ không được stage lại; dùng thông điệp commit riêng cho phần email nếu muốn.
Khi kiểm tra và commit đã xong, một lần push sẽ đưa các commit cục bộ còn thiếu lên nhánh riêng:

```powershell
git push origin backend/lam
```

Các file `.patch`, database và thư mục chứa file upload không cần đưa vào commit. Push nhánh riêng không tự merge vào `master`.

## Tài liệu tham khảo

- Django giao dịch và on_commit: https://docs.djangoproject.com/en/6.1/topics/db/transactions/
- Django Admin save_model: https://docs.djangoproject.com/en/6.1/ref/contrib/admin/#django.contrib.admin.ModelAdmin.save_model
