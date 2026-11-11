# Công việc Backend 2 có thể hoàn thành khi chưa có Ticket model

Bản vá được chuẩn bị từ master `2b6a71f0e856c813ca2018936fe34eadff37833a`.

## 1. Phạm vi và thứ tự

| Thứ tự | Phần việc | Kết quả kiểm tra |
| --- | --- | --- |
| Đã có | KB HTML, tìm kiếm, phân trang và API đọc | Chạy bộ test kb |
| Đã có | Kiểm tra định dạng/nội dung/dung lượng tệp | Chạy tickets.test_attachment_validation |
| 1 | Dịch vụ email, mẫu tiếng Việt, xem trước | Chạy test notifications; xem ba mẫu email |
| 2 | Dữ liệu KB mẫu dùng chung cho nhóm | seed_kb_demo; kiểm tra /kb/ và API |
| 3 | GitHub Actions chạy kiểm thử | Backend tests xuất hiện trong Actions sau push |
| 4 | Hợp đồng tích hợp email/tệp với BE1 | Bàn giao BACKEND2_INTEGRATION.md |

Phần email nhận các giá trị chuỗi, không import hoặc giả lập model Ticket.
Phần lưu tệp thật, quyền tải tệp, sự kiện phân công và chuyển trạng thái sẽ được nối với model/luồng nghiệp vụ do BE1 cung cấp.

## 2. Áp dụng bản vá trên Windows

Trong terminal VS Code, tại thư mục chứa manage.py:

```powershell
git status
git switch backend/lam
git fetch origin
git merge --no-edit origin/master
```

Hoàn tất hoặc commit các thay đổi mã nguồn đang làm trước khi merge. Nếu có CONFLICT, xử lý xong rồi mới áp dụng bản vá.
Tải backend2-independent-work.patch và đặt cạnh manage.py.

```powershell
Test-Path .\backend2-independent-work.patch
git apply --check .\backend2-independent-work.patch
```

Test-Path phải trả True. Chỉ áp dụng khi --check không báo lỗi:

```powershell
git apply .\backend2-independent-work.patch
git status
```

Các file chính mới: notifications/, kb/demo_content.py, kb/management/, kb/test_demo_content.py, .github/workflows/backend-tests.yml và hai tài liệu Backend 2.
helpdesk_system/settings.py được bổ sung app notifications và DEFAULT_FROM_EMAIL. Không thêm model hoặc migration.

## 3. Kiểm thử trước khi dùng

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test notifications kb.test_demo_content
.\.venv\Scripts\python.exe manage.py test kb accounts tickets notifications
```

Chạy từng lệnh. Kết quả kiểm thử cần là OK; lệnh kiểm tra migration cần báo No changes detected.
Nếu thiếu Pillow hoặc pypdf khi import test tệp, cài bộ phụ thuộc đã có của dự án:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-attachments.txt
```

16 kiểm thử mới gồm 12 test email và 4 test dữ liệu KB. Kết quả xác minh cuối cùng được ghi trong phần 9.

## 4. Xem trước email

Xem nội dung văn bản của ba sự kiện:

```powershell
.\.venv\Scripts\python.exe manage.py preview_ticket_email created
.\.venv\Scripts\python.exe manage.py preview_ticket_email assigned
.\.venv\Scripts\python.exe manage.py preview_ticket_email resolved
```

Lưu và mở bản HTML bằng trình duyệt:

```powershell
.\.venv\Scripts\python.exe manage.py preview_ticket_email created --html-output "$env:TEMP\helpdesk-created.html"
Start-Process "$env:TEMP\helpdesk-created.html"
```

Có thể đổi created thành assigned hoặc resolved và chọn tên file khác.
Lệnh dùng dữ liệu giả HD-DEMO-001, không gửi email và không tạo ticket. Đường dẫn trong thư là minh họa.
Các mẫu hỗ trợ cả HTML và văn bản thuần; nội dung nhập từ người dùng được escape trong bản HTML.

## 5. Tạo dữ liệu KB dùng chung

Đảm bảo database đã có các bảng Django:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_kb_demo --dry-run
```

Lệnh --dry-run chỉ thông báo các bài sẽ được tạo.
Để thêm 7 bài mẫu và hiển thị trên KB/API:

```powershell
.\.venv\Scripts\python.exe manage.py seed_kb_demo --publish
```

Các tiêu đề có tiền tố [Mẫu] để dễ nhận biết. Các chủ đề là Wi-Fi mất kết nối, LAN, Wi-Fi chậm, VPN, máy in, website nội bộ và thư mục dùng chung.
Chạy lại sẽ bỏ qua bài có cùng tiêu đề; nội dung, trạng thái xuất bản và ngày cập nhật của bài đã có được giữ nguyên.

Nếu muốn duyệt nội dung trước, dùng seed_kb_demo không có --publish để tạo bản nháp. Sau đó mở admin để xuất bản các bài cần dùng.
--publish chỉ áp dụng cho bài được tạo mới. Nó không xuất bản lại các bản nháp đã có.

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Đăng nhập tại http://127.0.0.1:8000/accounts/login/ rồi mở:
- http://127.0.0.1:8000/kb/
- http://127.0.0.1:8000/api/kb/articles/

Tìm từ khóa [Mẫu]. Nếu có đủ 7 bài đã xuất bản, trang đầu có 6 bài và trang sau có 1 bài.
Dữ liệu mẫu được tạo trong database của máy chạy lệnh; các thành viên khác cần tự chạy lệnh này sau khi lấy code.

## 6. GitHub Actions

Workflow .github/workflows/backend-tests.yml chạy khi push lên master/backend/lam, khi tạo PR vào master, hoặc chạy thủ công trong Actions.
Workflow dùng Python 3.13, cài hai file requirements hiện có, kiểm tra Django/migration rồi chạy test kb accounts tickets notifications.
Do requirements.txt có mysqlclient, runner cài thư viện hệ thống cần thiết để build driver. Các test hiện tại vẫn dùng SQLite.
actions/checkout và actions/setup-python được ghim vào commit của bản v6 đã xác minh.

Sau khi push, mở trang repository > Actions > Backend tests > lần chạy mới nhất.
Chỉ ghi nhận CI đã thành công khi lần chạy thực tế trên GitHub hiện dấu tích xanh.
Kiểm tra cấu trúc YAML và chạy lệnh test trên máy cục bộ chưa thay thế cho một lần chạy GitHub runner.

## 7. Commit và push

Dừng runserver bằng Ctrl+C hoặc mở terminal thứ hai, rồi kiểm tra:

```powershell
git diff --check
git status
git add notifications kb/management kb/demo_content.py kb/test_demo_content.py helpdesk_system/settings.py .github/workflows/backend-tests.yml BACKEND2_INDEPENDENT_WORK.md BACKEND2_INTEGRATION.md
git diff --cached --stat
git commit -m "feat: add ticket notifications, KB demo data and backend CI"
git push origin backend/lam
```

Giữ các file .patch ngoài commit; lệnh git add ở trên chỉ chọn mã nguồn, workflow và tài liệu.
Tạo PR backend/lam -> master sau khi các kiểm tra trên máy và workflow GitHub thành công.

## 8. Minh chứng và bàn giao

Có thể gửi nhóm trưởng: ảnh kết quả test OK, ảnh ba mẫu email, ảnh KB có bài [Mẫu], ảnh workflow xanh, URL commit và PR.
Với email, báo cáo là đã hoàn thành dịch vụ/mẫu/kiểm thử; việc tự động gửi theo Ticket và SMTP thực tế là phần tích hợp tiếp theo.
Bàn giao BACKEND2_INTEGRATION.md cho BE1 và BACKEND2_KB_API.md cho frontend.

Các mở rộng tùy nhu cầu và thống nhất của nhóm: phân loại bài KB theo nhóm sự cố, quản lý quyền biên tập/xuất bản, thêm trang KB trong React.
Chúng cần yêu cầu hoặc phối hợp giao diện cụ thể, không phải điều kiện để nghiệm thu gói hiện tại.

## 9. Xác minh

- Source nền: master 2b6a71f0e856c813ca2018936fe34eadff37833a.
- Python 3.13.5, Django 6.1.2, SQLite, Pillow 13.0.0, pypdf 6.21.4.
- Check Django và migration: thành công, không tạo migration mới.
- Bộ kiểm thử đầy đủ: 85 test, bao gồm 16 test mới, kết quả OK.
- Workflow YAML và SHA hai GitHub Actions: đã kiểm tra; lần chạy GitHub runner cần xác nhận sau khi push.
- Bản vá được kiểm tra trên file xuống dòng LF và CRLF trước khi bàn giao.

## Tài liệu tham khảo

- https://docs.djangoproject.com/en/6.1/topics/email/
- https://docs.djangoproject.com/en/6.1/topics/db/transactions/#performing-actions-after-commit
- https://docs.github.com/en/actions/tutorials/build-and-test-code/python
- https://github.com/PyMySQL/mysqlclient/blob/main/README.md
