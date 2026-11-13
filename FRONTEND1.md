# Frontend 1 — Giao diện Django của Minh Khôi

Bản cập nhật ngày 13/11/2026, dựa trên `master` tại `7b9b63b` sau khi nhóm ghép Backend 1 và Backend 2. Phạm vi theo tài liệu “ĐỀ TÀI NHÓM 2”: trang chủ/bố cục chung, tạo ticket, danh sách cá nhân kèm tiến độ và phản hồi, kết nối backend. Giao diện dùng Django Templates và Bootstrap 5.

## Trạng thái bàn giao

| Nhiệm vụ | Hiện trạng |
| --- | --- |
| Trang chủ, layout, sidebar, header, theme | Đã có giao diện và điều hướng dùng chung; hiển thị tài khoản, đăng xuất, menu điện thoại |
| Tạo yêu cầu sự cố | Form kiểm tra dữ liệu, giữ dữ liệu chữ khi nhập sai; gọi dịch vụ tạo Ticket và lưu file của backend |
| Danh sách ticket cá nhân | Truy vấn database theo quyền backend; tìm mã/tiêu đề/vị trí/người gửi, lọc trạng thái/nhóm/ưu tiên, sắp xếp và phân trang |
| Theo dõi và trao đổi | Hiển thị người phụ trách, trạng thái, lịch sử và bình luận từ database; phản hồi đã đóng bị từ chối |
| File đính kèm | Chọn/xem trước/bỏ file ở form; hiển thị tên, dung lượng và liên kết tải có kiểm tra quyền |
| Kết nối backend | Tái sử dụng Ticket, Comment, TicketHistory, Attachment và các dịch vụ Backend 1/2 đã cung cấp |

Người dùng thường chỉ thấy ticket của mình. Quyền của kỹ thuật viên/quản trị viên do backend quyết định; các endpoint phân công và đổi trạng thái vẫn thuộc luồng quản trị của nhóm.

## Hoàn thiện trong đợt này

- Đồng bộ lựa chọn nhóm sự cố và mức ưu tiên của form với model Ticket.
- Thống kê và thông báo chọn file hiển thị đúng chế độ dữ liệu thật/xem thử.
- Khi form có lỗi, nhắc chọn lại file trước khi gửi vì trình duyệt không giữ lựa chọn file sau khi tải lại.
- Hiển thị đúng người phụ trách đã lưu, kể cả khi trạng thái vẫn là “Chờ tiếp nhận”.
- Tìm được họ tên đầy đủ đang hiển thị của người gửi; xử lý từ khóa như `²`, `HD-²` và mã số quá lớn mà không làm lỗi trang.
- Giữ thứ tự phân trang ổn định khi nhiều ticket có cùng thời gian tạo.
- Nếu lưu phản hồi gặp lỗi database, hiển thị lỗi ngay tại form và giữ nội dung để người dùng gửi lại.
- Lấy danh sách phản hồi một lần khi render phần trao đổi.
- Thêm kiểm thử luồng người dùng với database thật, file thật, đổi phiên đăng nhập và nhiều tài khoản.

## Chạy trên Windows PowerShell

Bản cập nhật này không thêm thư viện hoặc migration. Dùng môi trường Python đã cài đủ thư viện của dự án; nếu đang dùng venv thì kích hoạt venv trước.

Trong thư mục chứa `manage.py`, chạy từng lệnh và chỉ tiếp tục khi lệnh trước thành công:

```powershell
python manage.py migrate
python manage.py check
python manage.py test tickets accounts kb notifications
python manage.py runserver
```

`migrate` áp dụng các migration Backend 1/2 đã có, bao gồm vai trò/tài khoản, Ticket/Comment/TicketHistory và Attachment. Không cần tạo migration mới cho thay đổi Frontend 1 này.

Mở http://127.0.0.1:8000/ và đăng nhập. Giữ terminal chạy server; `Ctrl+C` để dừng.

## Chế độ dữ liệu

- Cấu hình mặc định của backend dùng database thật: không khai báo `FRONTEND_DEMO_ENABLED`, hoặc đặt giá trị `None`.
- `FRONTEND_DEMO_ENABLED=True` chỉ dành cho chế độ xem thử và các kiểm thử cũ. Ticket/phản hồi của chế độ này nằm trong session, file chỉ có metadata.
- `FRONTEND_DEMO_ENABLED=False` giữ hành vi cũ là chặn các trang ticket bằng 404; không dùng giá trị này để bật database thật.
- Ticket thật vẫn còn sau khi đăng xuất/đăng nhập lại; dữ liệu demo cũ không tự chuyển thành ticket thật.
- File thật được lưu tại vùng riêng của backend và tải qua `tickets:attachment_download`; không tạo liên kết trực tiếp đến thư mục lưu file.
- Email dùng cấu hình backend của nhóm. Cấu hình phát triển hiện in email ở terminal; gửi SMTP thực tế cần nhóm cấu hình riêng.

## Kiểm tra trước khi nghiệm thu trên máy nhóm

1. Đăng nhập bằng tài khoản người dùng thường; mở trang chủ và “Ticket của tôi”. Thống kê phải đúng dữ liệu của tài khoản.
2. Tạo ticket với đủ trường, chọn một file hợp lệ. Trang chi tiết phải có mã ticket, thông tin sự cố và liên kết tải file.
3. Thử mô tả quá ngắn/file không hợp lệ. Form phải báo lỗi, giữ dữ liệu chữ và nhắc chọn lại file.
4. Đăng xuất rồi đăng nhập lại; ticket và file vừa tạo vẫn phải còn.
5. Nhờ kỹ thuật viên phân công/cập nhật trạng thái bằng luồng backend hoặc Django Admin của nhóm, rồi tải lại trang chi tiết. Kiểm tra tên người phụ trách, tiến độ và lịch sử thực tế.
6. Gửi phản hồi từ người dùng và kỹ thuật viên; tải lại trang không tạo thêm bản sao phản hồi. Ticket đã đóng không cho gửi thêm.
7. Thử tìm theo mã và họ tên đầy đủ, phối hợp các bộ lọc, đổi thứ tự và chuyển trang.
8. Đăng nhập bằng tài khoản người dùng khác: không thấy ticket riêng trong danh sách/thống kê và không truy cập được URL chi tiết, phản hồi hoặc tải file.
9. Thử màn hình điện thoại, menu, nội dung dài, lỗi form và thao tác khi tắt JavaScript.

## Xác minh kỹ thuật

- Nền kiểm thử: Python 3.12.14, Django 6.1.2, asgiref 3.13.0, sqlparse 0.6.0, Pillow 13.0.0, pypdf 6.21.4; database SQLite.
- Bộ kiểm thử nền của nhóm có 164 ca. Đợt này bổ sung 6 ca trong `tickets/test_frontend_integration.py`.
- Tổng cộng 170 kiểm thử đạt. `manage.py check`, `makemigrations --check --dry-run` và kiểm tra cú pháp JavaScript đều đạt; không có migration mới.
- Các ca mới kiểm tra luồng tạo/lưu/tải file/đổi phiên đăng nhập, cập nhật từ kỹ thuật viên, phản hồi, đóng ticket, cách ly tài khoản, tìm kiếm, phân trang và lỗi lưu phản hồi.
- Kiểm thử email dùng hộp thư bộ nhớ, không gửi email ra bên ngoài.
- Cần kiểm tra lại giao diện trực tiếp trên Windows/điện thoại và môi trường MySQL của nhóm trước khi nghiệm thu. Kết quả kiểm thử SQLite không thay thế việc đó.

## Điểm nối đang sử dụng

| Chức năng frontend | Backend hiện có |
| --- | --- |
| Tạo ticket và file | `tickets.attachment_services.create_ticket_with_attachment` |
| Danh sách và thống kê | QuerySet của `tickets.models.Ticket`, lọc theo quyền |
| Người gửi, người phụ trách, tiến độ | Các thuộc tính của Ticket: `reporter`, `assignee_name`, `status_label`, `steps` |
| Lịch sử | `TicketHistory` qua `ticket.events` |
| Phản hồi | `Comment` và `ticket.replies` |
| Tải file | `tickets:attachment_download`, kiểm tra quyền tại backend |
| Thông báo email | Các dịch vụ sự kiện do Backend 2 nối vào thao tác lưu ticket/phân công/trạng thái |
