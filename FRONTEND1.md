# Frontend 1 — Bước 1: Trang chủ và bố cục chung

Phần này bổ sung trang chủ tiếng Việt, header, sidebar và bố cục thích ứng với màn hình nhỏ bằng Django Template và Bootstrap 5.3.8. Đây là mốc đầu tiên để học và phát triển phần giao diện người dùng. Form tạo ticket và danh sách ticket sẽ được bổ sung sau.

## Chạy trên Windows Command Prompt

Mở Terminal tại thư mục chứa `manage.py`. Nếu Django đã được cài trong `.venv`, chạy:

```bat
.venv\Scripts\activate.bat
python manage.py check
python manage.py runserver
```

Mở http://127.0.0.1:8000/. Nếu mới lấy mã nguồn và chưa khởi tạo cơ sở dữ liệu, chạy `python manage.py migrate` trước `runserver`.

Bootstrap dùng CDN nên trình duyệt cần Internet để tải CSS và JavaScript của Bootstrap.

## Các file cần hiểu

| File | Vai trò |
| --- | --- |
| `templates/base.html` | Khung HTML chung gồm header, sidebar, nội dung và footer. |
| `templates/tickets/home.html` | Nội dung trang chủ, kế thừa `base.html`. |
| `static/css/site.css` | Màu sắc, khoảng cách và bố cục theo kích thước màn hình. |
| `static/js/site.js` | Đóng menu trên điện thoại sau khi chọn liên kết. |
| `tickets/views.py` | Hàm `home` trả về trang HTML. |
| `tickets/urls.py` | Đặt tên và ánh xạ đường dẫn tới hàm `home`. |
| `helpdesk_system/urls.py` | Kết nối đường dẫn của app `tickets` với dự án. |
| `helpdesk_system/settings.py` | Đăng ký app `tickets` và thư mục template, static. |

Luồng chạy: trình duyệt mở `/` → `helpdesk_system/urls.py` → `tickets/urls.py` → `home` trong `tickets/views.py` → `home.html` kế thừa `base.html`.

## Tự kiểm tra và thực hành

1. Mở trang chủ và xác nhận không còn màn hình tên lửa Django.
2. Bấm “Nhóm sự cố” và “Thông tin cần chuẩn bị” để chuyển đến đúng mục.
3. Thu hẹp cửa sổ trình duyệt; bấm nút menu để mở và đóng sidebar.
4. Sửa tiêu đề trong `home.html`, lưu file rồi tải lại trang để thấy thay đổi.
5. Đổi biến `--brand` trong `site.css` để hiểu cách chỉnh màu giao diện.

## Các bước tiếp theo của Frontend 1

1. Thêm trang tạo ticket: tiêu đề, mô tả, loại sự cố, độ ưu tiên và file đính kèm.
2. Thêm danh sách ticket cá nhân và giao diện xem trạng thái, phản hồi.
3. Thống nhất với Backend 1 về tên trường, URL và dữ liệu; phối hợp Backend 2 về file đính kèm.
4. Ghép dữ liệu thật, kiểm tra trạng thái trống, lỗi nhập liệu và màn hình nhỏ.

Trang chủ hiện chưa truy vấn dữ liệu ticket và chưa xử lý tạo ticket. Cấu hình cơ sở dữ liệu vẫn là SQLite như bộ khung repo; khi ghép dự án nhóm sẽ dùng cấu hình MySQL đã thống nhất.
