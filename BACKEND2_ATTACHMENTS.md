# Backend 2 — Kiểm tra tệp đính kèm

> Cập nhật: luồng lưu/tải tệp thật đã được nối vào Ticket của BE1.
> Xem [BACKEND2_TICKET_ATTACHMENTS.md](BACKEND2_TICKET_ATTACHMENTS.md) để cài đặt và kiểm tra bản hiện tại.
> Các mục bên dưới lưu lại phạm vi của bản vá kiểm tra định dạng ban đầu; không cần áp dụng lại bản vá cũ.

## Phần đã thực hiện

- Tách `tickets/attachment_validators.py` để dùng lại trong form và model sau này.
- Nối bộ kiểm tra vào `TicketForm.clean_attachment()` hiện có.
- Giữ giới hạn 1 file và 10 * 1024 * 1024 byte như giao diện.
- Chấp nhận JPG/JPEG/PNG/PDF/TXT/LOG, không phân biệt chữ hoa/thường của đuôi file.
- Đọc ảnh bằng Pillow, đối chiếu định dạng thực tế với đuôi file, kiểm tra cấu trúc và dữ liệu ảnh. Giới hạn ảnh 20 triệu điểm ảnh trước khi giải mã.
- Đọc cấu trúc PDF bằng pypdf ở chế độ strict. Tạm từ chối PDF bị lỗi, PDF không có trang và PDF mã hóa/có mật khẩu; người dùng nhận lỗi tại trường file.
- TXT/LOG chấp nhận UTF-8 (có hoặc không BOM) và UTF-16 có BOM. Từ chối dữ liệu chứa ký tự điều khiển nhị phân, ngoại trừ tab và xuống dòng.
- Từ chối file rỗng và file vượt dung lượng. Không dựa vào MIME do trình duyệt khai báo.
- Giữ nguyên nội dung file, trạng thái mở và vị trí đọc để bước lưu file sau này nhận đủ dữ liệu.
- Thêm 24 ca kiểm thử trong `tickets/test_attachment_validation.py`, gồm cả tích hợp với form.

## Áp dụng bản vá

Đặt `backend2-attachment-validation.patch` cạnh `manage.py`.
Đứng tại thư mục gốc dự án trong terminal VS Code, trên nhánh riêng đang dùng.

```powershell
git status
git apply --check backend2-attachment-validation.patch
```

Nếu lệnh kiểm tra không báo lỗi, áp dụng:

```powershell
git apply backend2-attachment-validation.patch
.\.venv\Scripts\python.exe -m pip install -r requirements-attachments.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test tickets.test_attachment_validation
```

Nếu kiểm tra bản vá báo lỗi, giữ lại thông báo để đối chiếu phiên bản code hiện tại. Bản vá được tạo theo nội dung `tickets/forms.py` đã cung cấp; không cần ghi đè file bằng tay.

File `requirements-attachments.txt` chỉ chứa hai thư viện bổ sung. Khi thiết lập máy khác, vẫn cài bộ requirements của dự án và cài thêm file này. Không cần migration cho thay đổi này.

Sau khi 24 test mới đạt, kiểm tra cả những phần liên quan của nhóm:

```powershell
.\.venv\Scripts\python.exe manage.py test tickets kb
```

Nếu test cũ dùng chuỗi byte bất kỳ nhưng đặt tên `.png`/`.pdf`, cần thay fixture đó bằng ảnh/PDF thật khi kiểm tra trường hợp hợp lệ. Bộ kiểm tra mới chủ động từ chối file giả định dạng. Không xóa kiểm thử cũ để bỏ qua lỗi.

## Thử trên trình duyệt

1. Chọn ảnh JPG/PNG hoặc PDF thật dưới 10 MB, điền đủ dữ liệu và tạo ticket xem thử.
2. Chọn file TXT/LOG UTF-8 hợp lệ và thử lại.
3. Đổi tên một file TXT thành `.png`, thử tạo ticket: backend phải báo lỗi tại trường file dù JavaScript bị tắt.
4. Thử file vượt 10 MB: có thông báo lỗi.
5. Bỏ trống trường file: vẫn tạo được ticket xem thử khi các trường còn lại hợp lệ.

Thông báo xem thử và help text về việc chưa lưu nội dung file vẫn đúng với phạm vi hiện tại.

## Chưa tích hợp lưu và tải file thật

`tickets/models.py` hiện chưa có Ticket. View đang lưu ticket vào Django session và chỉ lưu `attachment.name` cùng `attachment.size`. Bộ kiểm tra này không tạo bản ghi Ticket/Attachment và không lưu byte của file.

Trước khi nối lưu thật, nhóm cần thống nhất:

1. Tên model Ticket và trường chỉ người tạo/chủ ticket.
2. Quy tắc người dùng, kỹ thuật viên, quản trị được xem ticket nào.
3. Nơi lưu tệp riêng tư và vòng đời/xóa file khi thao tác lưu không hoàn tất.

Sau đó Backend 2 bổ sung model Attachment, liên kết bằng ForeignKey tới Ticket, lưu file bằng tên do server tạo, và route tải kiểm tra quyền xem ticket. File nên được trả dưới dạng tải xuống; URL media công khai không thay thế kiểm tra quyền.

Chỉ nối email sau khi lưu ticket thật thành công; không gửi email kỹ thuật cho dữ liệu session xem thử.

Kiểm tra định dạng không phải quét mã độc. PDF có cấu trúc đọc được hoặc ảnh đọc được vẫn không có nghĩa là mọi nội dung bên trong đều vô hại.

## Phạm vi đã xác minh khi tạo bản vá

- Python 3.12.14, Django 6.1.2, Pillow 13.0.0, pypdf 6.21.4.
- 24 test mới đạt, không dùng database.
- Form kiểm tra là form được cung cấp, với các choice `category`/`priority` theo FRONTEND1.md trong một dự án kiểm chứng tối giản.
- Chưa nhận toàn bộ repository và các test có sẵn của nhóm, vì vậy cần chạy `test tickets kb` trên dự án thật trước khi merge.

## Tài liệu tham khảo

- Django file uploads: https://docs.djangoproject.com/en/6.1/topics/http/file-uploads/
- Pillow Image.verify / Image.load: https://pillow.readthedocs.io/en/stable/reference/Image.html
- pypdf PdfReader: https://pypdf.readthedocs.io/en/stable/modules/PdfReader.html
