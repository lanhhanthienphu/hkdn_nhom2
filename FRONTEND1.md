# Frontend 1 — Bàn giao giao diện của Khôi

Bản cập nhật tiếp tục `frontend/khoi` tại `0ad6658` và đã ghép `master` tại `5b49570`. Giữ Django Template, Bootstrap 5.3.8 và SQLite đang có. Việc xóa `requirements-frontend.txt` trên nhánh của Khôi được giữ nguyên.

## Phạm vi đã hoàn thành

| Phần | Kết quả |
| --- | --- |
| Bố cục chung | Trang chủ, header, sidebar, trạng thái menu, menu điện thoại, liên kết bỏ qua đến nội dung |
| Tài khoản | Giao diện đăng nhập/đăng ký đồng bộ, hiện/ẩn mật khẩu, lỗi tại trường, tên tài khoản và đăng xuất bằng POST |
| Trang chủ cá nhân | 5 ô thống kê theo trạng thái, 3 ticket gần đây, liên kết tạo ticket và các bài hướng dẫn đã xuất bản |
| Tạo ticket | Tiêu đề, nhóm, ưu tiên, vị trí, mô tả, chọn file; báo lỗi và giữ dữ liệu chữ khi nhập sai |
| File đính kèm | Kiểm tra đuôi/dung lượng, xem trước ảnh tại trình duyệt, bỏ file đã chọn |
| Ticket của tôi | Tìm theo mã/tiêu đề/vị trí/người gửi; lọc trạng thái, nhóm, ưu tiên; sắp xếp và phân trang |
| Chi tiết ticket | Tiến độ, người gửi, thông tin sự cố, lịch sử hoạt động, phản hồi; chặn phản hồi khi đã đóng |
| Kho kiến thức | Giữ chức năng của nhóm; nối menu, bài viết ở trang chủ và gợi ý tìm hướng dẫn theo nhóm sự cố |
| Trạng thái giao diện | Danh sách trống, không có kết quả, lỗi form, lỗi phiên/CSRF, ticket không tồn tại; mẫu trang 400/403/404/500 |
| Điện thoại / không có JavaScript | Bố cục 390 và 320 px; form, bộ lọc, phân trang và menu dự phòng vẫn sử dụng được |
| Tài nguyên | Bootstrap được lưu trong `static/vendor/bootstrap`, kèm giấy phép MIT; không cần tải CDN khi mở giao diện |

## Dữ liệu thật và phần còn chờ backend

**Đăng nhập, đăng ký, đăng xuất và Kho kiến thức đã dùng backend của nhóm.** Tài khoản được lưu trong database; trang chủ chỉ lấy bài hướng dẫn đã xuất bản. Đăng nhập giữ lại URL đích cùng vị trí/nhóm sự cố đã điền từ liên kết, đồng thời chặn chuyển hướng sang website bên ngoài.

**Ticket, thống kê ticket, tiến độ và phản hồi vẫn là bản xem thử.** Tại thời điểm ghép nhánh, `tickets/models.py` chưa có model Ticket. Chưa thể nghiệm thu phần tích hợp ticket thật; cần phối hợp với backend khi model/service sẵn sàng.

- Sáu ticket mẫu được tạo trong Django session của mỗi trình duyệt, gắn với tài khoản đang đăng nhập. Đổi tài khoản, đăng xuất, xóa cookie hoặc hết phiên có thể làm mất dữ liệu xem thử; dữ liệu này không đồng bộ giữa các thiết bị.
- Ticket/phản hồi tạo trong giao diện chưa được gửi đến kỹ thuật viên. Trạng thái mẫu được tạo sẵn; người dùng không tự đổi trạng thái.
- File chỉ lưu **tên và dung lượng** trong phiên. Ảnh xem trước chỉ ở trình duyệt; không lưu nội dung và chưa có chức năng tải file thật.
- Tối đa 30 ticket/phiên, 30 phản hồi/ticket. Giữ nhãn xem thử cho đến khi nối backend thật.
- Khi `FRONTEND_DEMO_ENABLED` chưa được khai báo, demo dùng giá trị `DEBUG`. Các trang ticket trả 404 khi demo bị tắt. Trang chủ và Kho kiến thức vẫn dùng được.
- Mẫu lỗi toàn hệ thống 400/404/500 được Django dùng khi `DEBUG=False`. Trang lỗi CSRF và ticket không tồn tại có giao diện riêng ngay cả lúc phát triển.
- Cấu hình hiện tại phục vụ phát triển tại máy; chưa phải bản triển khai production.

Bản cập nhật không thêm model Ticket, không sửa chức năng phân công/dashboard của Frontend 2, không thêm dịch vụ upload/email. Không chứa database, tài khoản thử, file đính kèm hay môi trường Python của máy kiểm thử.

## Chạy trên Windows PowerShell

Mở Terminal trong thư mục có `manage.py`. Dùng Python của cùng môi trường đã cài Django. Nếu dự án đã chạy được, không cần tạo lại môi trường hoặc cài lại thư viện.

Nếu chưa có `.venv`, tạo một lần:

```powershell
py -m venv .venv
```

Dự án đầy đủ dùng `requirements.txt` của nhóm:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu chỉ thử giao diện bằng SQLite và máy chưa cài được driver MySQL, có thể cài các thư viện Python sau với đúng phiên bản đang ghi trong `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -m pip install Django==6.1.2 asgiref==3.13.0 sqlparse==0.6.0 tzdata==2026.5
```

Đây là cách chạy SQLite cục bộ; môi trường MySQL vẫn cần driver theo cấu hình của nhóm. Sau khi đã có Django:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test tickets accounts kb
.\.venv\Scripts\python.exe manage.py runserver
```

Mở http://127.0.0.1:8000/. Đăng nhập tài khoản của bạn hoặc chọn **Đăng ký tài khoản**. Tài khoản đăng ký thường không có quyền quản trị. Giữ Terminal mở khi sử dụng; `Ctrl+C` để dừng server.

`migrate` chạy migration sẵn có của Django và Kho kiến thức; phần Frontend 1 này không tạo migration mới. Nếu kho chưa có bài đã xuất bản, giao diện hiển thị trạng thái trống thay vì tự tạo bài.

## Kiểm tra trước khi bàn giao

1. Mở `/tickets/new/?location=A.201&category=network` khi chưa đăng nhập. Sau đăng nhập, form vẫn giữ phòng A.201 và nhóm Mạng LAN / Wi-Fi.
2. Thử mật khẩu sai và đăng ký dữ liệu không hợp lệ; kiểm tra lỗi, nhãn trường và nút hiện/ẩn mật khẩu.
3. Ở trang chủ, kiểm tra thống kê, ticket gần đây và liên kết Kho kiến thức.
4. Tạo ticket với dữ liệu hợp lệ; thử trường bắt buộc, mô tả dưới 20 ký tự, file sai đuôi hoặc trên 10 MB.
5. Chọn ảnh JPG/PNG để xem trước; bỏ ảnh, chọn lại file và gửi. Trang chi tiết có mã ticket, người gửi, trạng thái và metadata file.
6. Thêm phản hồi, tải lại trang; phản hồi không bị gửi thêm lần nữa. Ticket đã đóng không có form phản hồi.
7. Tìm theo mã ticket, thử phối hợp các bộ lọc, đổi thứ tự và chuyển trang. Kiểm tra trường hợp không có kết quả.
8. Kiểm tra Kho kiến thức có tìm kiếm và trang bài viết. Bài nháp không xuất hiện ở trang chủ.
9. Đăng xuất; mở lại trang ticket phải đăng nhập. Không coi dữ liệu mẫu là dữ liệu ticket được lưu lâu dài.
10. Thử màn hình 390 và 320 px; mở menu. Tắt JavaScript để thử tạo ticket, phản hồi và điều hướng bằng menu dự phòng.

Liên kết điền sẵn vị trí chỉ hỗ trợ bước chuẩn bị cho QR; chưa có chức năng sinh/quản lý mã QR. `127.0.0.1` trên điện thoại không trỏ về máy tính chạy Django.

## Điểm nối với backend

Tên trường dưới đây là hợp đồng đề xuất của giao diện, cần thống nhất với backend trước khi tích hợp:

| Trường | Giá trị giao diện |
| --- | --- |
| `title` | Chuỗi 5–150 ký tự |
| `description` | Chuỗi 20–5.000 ký tự |
| `location` | Chuỗi bắt buộc, tối đa 100 ký tự |
| `category` | `network`, `vpn`, `printer`, `other` |
| `priority` | `low`, `normal`, `high`, `urgent` |
| `status` | `new`, `in_progress`, `resolved`, `closed`; do backend quản lý |
| `attachment` | 1 file JPG/JPEG/PNG/PDF/TXT/LOG, tối đa 10 MB |
| Phản hồi `content` | Chuỗi 3–2.000 ký tự |
| Người gửi | Lấy từ `request.user`, không tin giá trị do form gửi lên |

Khi backend có model/service:

1. Thay lời gọi `demo_store` trong `tickets/views.py` bằng truy vấn/service thật; giữ template và các URL đang dùng.
2. Giới hạn danh sách, xem chi tiết, phản hồi và tải file theo quyền của người đăng nhập; kiểm tra quyền cả GET và POST.
3. Ánh xạ trường form, trạng thái, người phụ trách, thời gian và lịch sử từ backend. Cập nhật thống kê và danh sách gần đây từ cùng nguồn dữ liệu.
4. Nối upload/download và kiểm tra nội dung file phía server. Kiểm tra đuôi file trong bản xem thử không thay cho kiểm tra upload thật.
5. Nối phản hồi, thông báo lỗi và các tình huống xung đột trạng thái. Chỉ bỏ nhãn xem thử sau khi dữ liệu thật được lưu thành công.
6. Khôi cùng backend kiểm thử bằng ít nhất hai tài khoản; kiểm tra không đọc hoặc sửa ticket của người khác và dữ liệu vẫn còn sau đăng nhập lại.

## File chính và kết quả kiểm tra

| File / thư mục | Vai trò |
| --- | --- |
| `templates/base.html`, `static/css/site.css` | Bố cục và menu dùng chung |
| `templates/tickets/`, `static/css/tickets.css` | Trang chủ và các trang ticket |
| `static/css/portal.css` | Tài khoản, thống kê, bài hướng dẫn, lỗi và điều chỉnh mobile |
| `static/js/tickets.js`, `static/js/auth.js` | Tăng tiện ích cho form, ảnh xem trước, mật khẩu |
| `accounts/templates/accounts/`, `accounts/forms.py` | Giao diện tài khoản dùng chức năng auth của nhóm |
| `accounts/middleware.py`, `accounts/views.py` | Giữ URL đích sau xác thực và đăng ký |
| `tickets/forms.py`, `tickets/views.py` | Kiểm tra nhập liệu, xử lý form, lọc và render |
| `tickets/demo_store.py` | Nguồn dữ liệu mẫu tách riêng, thay khi có backend |
| `helpdesk_system/error_views.py`, `templates/errors/` | Trang lỗi CSRF và bố cục lỗi dùng chung |
| `static/vendor/bootstrap/` | Bootstrap 5.3.8 và giấy phép MIT |
| `tickets/tests.py`, `accounts/tests.py` | Kiểm thử hành vi ticket và tích hợp tài khoản |

26 ca kiểm thử Django đạt trên SQLite. `manage.py check`, kiểm tra cú pháp JavaScript và `pip check` đạt. Đã kiểm tra Chromium trên desktop, 390 px và 320 px: đăng nhập/đăng ký, URL có vị trí, tạo ticket, chọn/bỏ file, phản hồi, bộ lọc, Kho kiến thức và menu. Form và điều hướng cũng được kiểm tra khi tắt JavaScript. Chưa kiểm thử MySQL hoặc backend ticket thật.
