# Frontend 1 — Trang chủ và luồng ticket

Bản cập nhật này tiếp tục nhánh `frontend/khoi` tại commit `a72e8c2`, giữ Django Template + Bootstrap 5.3.8 và phong cách giao diện đang có.

## Phần đã có

| Phần | Trạng thái |
| --- | --- |
| Trang chủ, header, sidebar, menu điện thoại | Có, bổ sung liên kết tới các trang ticket |
| Tạo ticket | Có tiêu đề, nhóm sự cố, ưu tiên, vị trí, mô tả và chọn 1 file |
| Kiểm tra nhập liệu | Có trên trình duyệt và Django; báo lỗi tại trường, giữ lại dữ liệu chữ |
| Ticket của tôi | Có tìm theo mã/tiêu đề/vị trí, lọc trạng thái/nhóm, sắp xếp, phân trang |
| Chi tiết ticket | Có tiến độ, mô tả, thông tin file, lịch sử hoạt động và phản hồi |
| Các trạng thái giao diện | Có lỗi form, chưa có ticket, không có kết quả, ticket đã đóng |
| Giao diện điện thoại | Có bố cục thẻ, bộ lọc và menu thu gọn |

## Giới hạn của bản xem thử

Các trang ticket sử dụng dữ liệu mẫu trong **Django session của từng trình duyệt**. Sáu ticket ban đầu dùng để kiểm tra các trạng thái. Ticket và phản hồi bạn thêm chỉ xuất hiện trong phiên của bạn. Nếu xóa cookie, đổi trình duyệt hoặc hết phiên, bạn sẽ không thấy các ticket xem thử trước đó.

- Chưa có model Ticket hay hệ thống phân công thật; nút tạo và phản hồi không gửi yêu cầu đến kỹ thuật viên.
- File được kiểm tra đuôi và dung lượng, nhưng **chỉ tên và dung lượng được lưu vào phiên**. Không lưu nội dung và không tạo đường dẫn tải file.
- Trạng thái của ticket mẫu được tạo sẵn; ticket mới giữ trạng thái Chờ tiếp nhận. Người dùng không tự đổi trạng thái.
- Không phải tính năng đăng nhập hay phân quyền. Khi nối dữ liệu thật, backend phải giới hạn dữ liệu theo người dùng đã đăng nhập.
- Tối đa 30 ticket/phiên, 30 phản hồi/ticket để giới hạn dung lượng dữ liệu xem thử.
- Trang ticket mặc định chỉ chạy khi `DEBUG=True`. Khi `DEBUG=False`, các URL này trả 404 trừ khi nhóm chủ động đặt `FRONTEND_DEMO_ENABLED=True`. Xóa hoặc thay lớp demo khi tích hợp backend.
- Bootstrap vẫn dùng CDN như bản trước; cần Internet để tải Bootstrap.

## Áp dụng bản cập nhật

Đặt `frontend1-tickets.patch` cạnh `manage.py`. Trong VS Code, đứng ở thư mục `hkdn_nhom2` trên nhánh `frontend/khoi` rồi chạy:

```powershell
git apply --check frontend1-tickets.patch
git apply frontend1-tickets.patch
```

Lệnh kiểm tra thành công sẽ không in gì. Nếu kiểm tra báo lỗi, dừng ở đó và gửi nội dung lỗi; không dùng lệnh khôi phục hay ghi đè các file đang sửa. Patch được tạo theo commit `a72e8c2` của nhánh này, chưa bao gồm thay đổi riêng chưa push trên máy bạn.

## Chạy trên Windows PowerShell

Dùng trực tiếp Python của dự án để tránh lỗi `No module named django` do chọn nhầm môi trường.

Nếu **chưa có** thư mục `.venv`, tạo một lần:

```powershell
py -m venv .venv
```

Sau đó chạy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-frontend.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Mở http://127.0.0.1:8000/. Giữ Terminal mở; `Ctrl+C` để dừng server.

`requirements-frontend.txt` giữ nguyên phiên bản Django và các thư viện Python của nhóm, chỉ bỏ driver MySQL khi chạy giao diện với SQLite. Khi tích hợp backend MySQL, dùng lại `requirements.txt` của nhóm. Không dùng danh sách frontend cho môi trường MySQL.

Nếu Django đã có trong `.venv`, có thể bỏ qua lệnh cài thư viện. `migrate` tạo các bảng session mặc định; bản này không thêm migration hay đổi database của nhóm.

## Thử theo thứ tự

1. Ở trang chủ, bấm **Báo sự cố mạng**: form mở với nhóm Mạng LAN / Wi-Fi được chọn sẵn.
2. Bấm tạo khi chưa nhập dữ liệu, kiểm tra trường bắt buộc.
3. Nhập tiêu đề tối thiểu 5 ký tự, mô tả tối thiểu 20 ký tự, phòng/vị trí và chọn ưu tiên.
4. Chọn file không đúng đuôi hoặc trên 10 MB để xem thông báo; sau đó chọn file hợp lệ hoặc bỏ file.
5. Bấm **Tạo ticket xem thử**. Trang chi tiết mở với mã ticket và trạng thái Chờ tiếp nhận.
6. Thêm phản hồi, tải lại trang; phản hồi vẫn nằm trong cùng phiên và không bị thêm lần nữa.
7. Vào **Ticket của tôi**, tìm bằng mã vừa tạo, thử lọc, sắp xếp và chuyển trang.
8. Tìm từ khóa không tồn tại để xem thông báo trống và nút Xóa bộ lọc.
9. Mở ticket mẫu đã đóng: không có form gửi phản hồi.
10. Thử màn hình 390 px và 320 px; mở menu, điều hướng giữa ba trang.

Có thể điền trước vị trí từ URL để chuẩn bị cho luồng quét QR:

```text
/tickets/new/?location=A.201&category=network
```

Đây chỉ là điền sẵn trường form, chưa phải hệ thống sinh/quản lý mã QR. Địa chỉ `127.0.0.1` trên điện thoại không trỏ về máy tính chạy Django.

## Các file chính

| File | Vai trò |
| --- | --- |
| `templates/base.html` | Bố cục chung, menu ticket và thông báo |
| `templates/tickets/home.html` | Trang chủ, liên kết tạo ticket theo nhóm |
| `templates/tickets/create.html` | Form báo sự cố |
| `templates/tickets/list.html` | Bộ lọc, danh sách, phân trang và trạng thái trống |
| `templates/tickets/detail.html` | Tiến độ, thông tin, phản hồi và lịch sử |
| `templates/tickets/_field.html`, `_errors.html`, `_demo_banner.html` | Thành phần giao diện dùng lại |
| `static/css/tickets.css` | Kiểu dáng các trang ticket và bố cục điện thoại |
| `static/js/tickets.js` | Đếm ký tự, kiểm tra file, trạng thái nút gửi |
| `tickets/forms.py` | Hợp đồng trường dữ liệu và kiểm tra phía Django |
| `tickets/views.py`, `tickets/urls.py` | Render trang, điều hướng, lọc và POST/redirect |
| `tickets/demo_store.py` | Dữ liệu mẫu tách riêng, cần thay khi nối backend |
| `tickets/tests.py` | Kiểm thử luồng tạo/xem/phản hồi, dữ liệu lỗi, CSRF, giới hạn và tách phiên |

## Hợp đồng để ghép với backend

| Trường | Kiểu / giá trị giao diện |
| --- | --- |
| `title` | Chuỗi 5–150 ký tự |
| `description` | Chuỗi 20–5.000 ký tự |
| `location` | Chuỗi bắt buộc, tối đa 100 ký tự |
| `category` | `network`, `vpn`, `printer`, `other` |
| `priority` | `low`, `normal`, `high`, `urgent` |
| `status` | `new`, `in_progress`, `resolved`, `closed` — do backend quản lý |
| `attachment` | 1 file JPG/JPEG/PNG/PDF/TXT/LOG, tối đa 10 MB |
| Phản hồi `content` | Chuỗi 3–2.000 ký tự |

Tên trường và danh mục trên là **đề xuất của phần giao diện**, chưa được xem là hợp đồng backend đã thống nhất. Khi nhóm có model/API:

1. Backend 1 thay dữ liệu session bằng model/service; nối danh sách theo `request.user` và kiểm tra quyền cả GET lẫn POST.
2. Thay `TicketForm` bằng ModelForm hoặc ánh xạ trường sang API đã thống nhất, giữ lỗi tại trường và mẫu HTML.
3. Backend 2 thực hiện lưu file thật, kiểm tra nội dung/loại file, giới hạn dung lượng và quyền tải file. Kiểm tra đuôi file của bản demo không thay thế kiểm tra an toàn upload thật.
4. Nối người phụ trách, trạng thái và lịch sử từ backend. Ticket đã xử lý/đóng phải được phân biệt theo quy tắc của nhóm.
5. Nối phản hồi thật, xử lý lỗi gửi và lỗi quyền truy cập; thay các nhãn xem thử khi chức năng thật hoàn tất.
6. Kiểm thử tài khoản khác nhau để đảm bảo không xem/sửa ticket của người khác.

Nhánh `master` tại lúc kiểm tra đã có phần Kho kiến thức của nhóm; bản patch này tiếp tục trực tiếp `frontend/khoi` và không đưa các thay đổi của Kho kiến thức vào. Khi ghép nhánh, giữ lại menu Kho kiến thức cùng menu ticket mới.

## Kiểm thử tự động

```powershell
.\.venv\Scripts\python.exe manage.py test tickets
```

Bản cập nhật được kiểm tra với Django 6.1.2 và SQLite: 11 ca kiểm thử đạt. Đã kiểm tra trên Chromium ở độ rộng 1.440, 390 và 320 px; thử tạo ticket, file sai định dạng, phản hồi, phân trang, menu điện thoại và tạo ticket khi tắt JavaScript. Các ca kiểm thử dùng database thử nghiệm riêng. Chưa kiểm thử tích hợp MySQL hoặc backend ticket thật. Các file dữ liệu SQLite, `.venv` và file người dùng chọn không nằm trong bản cập nhật.
