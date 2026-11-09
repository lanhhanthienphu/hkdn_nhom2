# API kho kiến thức — Backend 2

Bản bổ sung dựa trên master `526feb4aa9c78779be97cf44c94410ce6a47d03b`.
Dùng Django JsonResponse và model Article hiện có; không cần thêm thư viện hoặc migration.

## Phạm vi

- Đọc danh sách và chi tiết bài đã xuất bản, đăng nhập bằng session Django hiện có.
- Tìm trong title hoặc content; bỏ khoảng trắng đầu/cuối; sắp xếp -created_at, -pk.
- Mỗi trang tối đa 6 bài. next/previous là đường dẫn tương đối, giữ và mã hóa từ khóa q.
- Giao diện HTML /kb/ tiếp tục dùng các view và template hiện tại.
- Đây là API backend; trang React chưa tự động được nối với API.

## Các file

| File | Vai trò |
| --- | --- |
| kb/api.py | Kiểm tra đăng nhập, phương thức đọc, truy vấn Article và trả JSON |
| kb/api_urls.py | Định tuyến với namespace kb_api |
| kb/test_api.py | 12 kiểm thử API |
| helpdesk_system/urls.py | Thêm đường dẫn /api/kb/ |
| accounts/middleware.py | Người chưa đăng nhập vào /api/kb/ nhận JSON 401 |
| BACKEND2_KB_API.md | Hướng dẫn và hợp đồng dữ liệu |

## Endpoint

| Phương thức | Đường dẫn | Kết quả |
| --- | --- | --- |
| GET | /api/kb/articles/ | Danh sách bài đã xuất bản |
| GET | /api/kb/articles/?q=Wi-Fi&page=1 | Tìm kiếm và phân trang |
| GET | /api/kb/articles/1/ | Chi tiết bài có id=1 nếu đã xuất bản |

HEAD cũng được hỗ trợ, không trả body. Các thao tác ghi không được hỗ trợ.
Đăng nhập tại /accounts/login/ trên cùng trình duyệt và cùng tên máy chủ (ví dụ 127.0.0.1).

### JSON danh sách

Ví dụ minh họa với một bài; id và thời gian thực tế phụ thuộc cơ sở dữ liệu:

```json
{
  "query": "wifi",
  "count": 1,
  "page": 1,
  "page_size": 6,
  "num_pages": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Hướng dẫn wifi",
      "content": "Kiểm tra kết nối mạng.",
      "created_at": "2026-11-09T10:00:00Z",
      "updated_at": "2026-11-09T10:00:00Z"
    }
  ]
}
```

Chi tiết trả trực tiếp một đối tượng gồm id, title, content, created_at, updated_at.
Thời gian dùng định dạng ISO 8601 do Django JSON encoder cung cấp.
count là số bài sau khi lọc; page là trang thực tế được trả về.
Khi không có kết quả: count=0, results=[], page=1, num_pages=1, next=previous=null.

Phân trang dùng Paginator.get_page giống trang KB hiện tại:
- Thiếu page hoặc page không phải số: trả trang 1.
- page bằng 0, âm hoặc vượt số trang: trả trang cuối.
- Việc tìm kiếm có phân biệt dấu hay không phụ thuộc database; chưa bổ sung tìm tiếng Việt không dấu.

### Lỗi

| Trạng thái | error | Ý nghĩa |
| --- | --- | --- |
| 401 | authentication_required | Chưa đăng nhập, không chuyển sang HTML đăng nhập |
| 404 | not_found | Bài không tồn tại hoặc chưa xuất bản |
| 405 | method_not_allowed | Phương thức không phải GET/HEAD; header Allow: GET, HEAD |

Lỗi JSON có dạng {"error": "mã lỗi", "message": "thông báo tiếng Việt"}.
Các endpoint không ghi dữ liệu. CSRF middleware vẫn hoạt động; yêu cầu ghi thiếu CSRF token có thể bị chặn 403 trước khi đến view. Không thêm csrf_exempt.
Các đường dẫn không được định nghĩa vẫn dùng xử lý 404 chung của website.
Phản hồi API không được cache; nội dung bài nháp không được trả cho cả tài khoản staff khi gọi API đọc này.

## Kiểm thử trên Windows PowerShell

Chạy trong thư mục có manage.py, sau khi đã cài môi trường của dự án:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test kb.test_api
.\.venv\Scripts\python.exe manage.py test kb accounts tickets
.\.venv\Scripts\python.exe manage.py runserver
```

Chỉ chạy lệnh tiếp theo khi lệnh trước thành công. Test dùng cơ sở dữ liệu kiểm thử riêng.
12 test mới gồm đăng nhập/401, bảo vệ tại view, dữ liệu đã xuất bản, tìm kiếm, kết quả rỗng, chi tiết, 404, phân trang giữ q/thứ tự ổn định, page không hợp lệ, từ chối ghi, HEAD và giữ chuyển hướng trang HTML.
Đã kiểm tra trên bản sao source nêu trên: 69 kiểm thử tổng cộng đều OK, với Python 3.12.14, Django 6.1.2, Pillow 13.0.0 và pypdf 6.21.4. Vẫn cần chạy lại trên môi trường Windows của nhóm.

Kiểm tra bằng trình duyệt:
1. Đăng nhập http://127.0.0.1:8000/accounts/login/.
2. Mở http://127.0.0.1:8000/api/kb/articles/ và kiểm tra results.
3. Thử ?q=Wi-Fi&page=1; theo next để kiểm tra trang sau nếu có hơn 6 kết quả.
4. Lấy id thật trong results và mở /api/kb/articles/<id>/.
5. Thử bài nháp hoặc id không tồn tại để kiểm tra JSON 404.
6. Mở API trong cửa sổ ẩn danh chưa đăng nhập: nhận JSON 401.
7. Mở /kb/ trong cửa sổ đang đăng nhập: giao diện tìm kiếm/phân trang vẫn hoạt động.

## Bàn giao frontend

Frontend dùng trường results để vẽ danh sách, count/num_pages/page để hiển thị phân trang, next/previous để chuyển trang.
API dùng cookie session, chưa có JWT/token endpoint. Khi nối React chạy ở cổng khác, nhóm cần thống nhất dev proxy/cùng nguồn gốc và luồng đăng nhập gửi cookie; không giả định chỉ mở CORS là đã đăng nhập được.
Render title/content như văn bản; không chèn trực tiếp nội dung bài vào innerHTML.

## Tài liệu Django

- https://docs.djangoproject.com/en/6.1/ref/request-response/#jsonresponse-objects
- https://docs.djangoproject.com/en/6.1/ref/paginator/#django.core.paginator.Paginator.get_page
