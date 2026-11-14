# Backend 2 — Lọc báo cáo và xuất CSV

Bản vá `backend2-report-filters-csv.patch` dùng trên nền `master` tại `cf35d7db5dc30d945a5765c0a17c9da1cb832e50` (179 test).
Tiếp tục làm việc trên nhánh `backend/lam`. Bản vá bổ sung chức năng cho trang Báo cáo đang có, sử dụng model và quyền của hệ thống hiện tại.

## Chức năng

- Lọc báo cáo theo ngày tạo từ/đến, nhóm sự cố, người phụ trách, trạng thái và mức ưu tiên.
- Chọn riêng ticket chưa phân công; có thể lọc người phụ trách cũ đã bị vô hiệu hóa nếu vẫn còn ticket được gán.
- Các số tổng hợp, biểu đồ và bảng kỹ thuật viên lấy từ cùng tập ticket đã lọc.
- Xuất toàn bộ ticket phù hợp ra CSV, không giới hạn theo trang danh sách.
- CSV gồm 9 cột: mã, tiêu đề, nhóm, ưu tiên, trạng thái, vị trí, người gửi, người phụ trách và ngày tạo.
- File dùng UTF-8 có BOM để đọc tiếng Việt trong Excel; hỗ trợ dấu phẩy, dấu nháy và xuống dòng trong một ô.
- Bộ lọc sai được hiển thị lỗi, trả HTTP 400 và không xuất file hoặc tự chuyển sang báo cáo toàn bộ.
- Nút Về Dashboard dẫn qua bộ điều hướng theo vai trò, dùng được cho quản trị viên và kỹ thuật viên.

## Áp dụng từng bước trên Windows

1. Trong VS Code, Save All trước khi áp dụng. Đóng các tab đang mở `tickets/views.py`, `tickets/urls.py` và `templates/tickets/reports.html` để tránh lưu bản cũ trong editor đè lên bản mới sau khi áp dụng.
2. Đặt file patch cạnh `manage.py`.
3. Kiểm tra nhánh và thay đổi đang có:

```powershell
git status
```

Nhánh cần dùng là `backend/lam`. Nếu chỉ còn các file `.patch` chưa được theo dõi, có thể tiếp tục. Các thay đổi code đang sửa dở cần được giữ riêng trước khi áp dụng bản vá.

4. Kiểm tra bản vá:

```powershell
git apply --check .\backend2-report-filters-csv.patch
```

Lệnh thành công thường không in gì. Nếu báo lỗi, giữ thông báo để đối chiếu phiên bản code; không chép đè file hoặc dùng `--reject`.

5. Áp dụng rồi kiểm tra:

```powershell
git apply .\backend2-report-filters-csv.patch
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test kb accounts tickets notifications
```

Bản này không thêm migration hoặc thư viện. Bộ kiểm thử dự kiến có 206 ca trên nền 179 ca đã nêu. Chỉ tiếp tục khi kết quả `OK`.

6. Chạy server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

7. Đăng nhập quản trị viên rồi mở `http://127.0.0.1:8000/dashboard/reports/`.

## Kiểm tra trực tiếp để lấy minh chứng

1. Dùng các ticket đã có hoặc tạo hai ticket thử với nhóm khác nhau, ví dụ một ticket LAN/Wi-Fi và một ticket máy in. Có thể để một ticket chưa phân công, một ticket giao cho kỹ thuật viên.
2. Mở trang Báo cáo. Phía dưới tiêu đề phải có khung Lọc báo cáo với 6 trường và các nút Áp dụng bộ lọc, Xóa bộ lọc.
3. Chọn Từ ngày và Đến ngày bao gồm ngày tạo các ticket. Chọn một nhóm sự cố rồi bấm Áp dụng bộ lọc.
4. Đối chiếu số ticket phù hợp, các biểu đồ và bảng kỹ thuật viên. Chuyển sang Chưa phân công để kiểm tra nhóm ticket chưa có người phụ trách.
5. Bấm Xuất CSV. Mở bằng Excel hoặc trình đọc CSV; đối chiếu mã ticket, nhóm, trạng thái và người phụ trách với bộ lọc vừa áp dụng. File có một hàng tiêu đề cộng với số ticket phù hợp tại thời điểm tải.
6. Chọn một tổ hợp bộ lọc không có dữ liệu. Trang phải báo không có ticket phù hợp; CSV vẫn tải được và chỉ có hàng tiêu đề.
7. Nhập Từ ngày sau Đến ngày rồi áp dụng. Trang phải báo lỗi ngay trên form, giữ giá trị đã nhập và không hiện nút xuất CSV.
8. Bấm Xóa bộ lọc để trở lại báo cáo toàn bộ.
9. Dùng tài khoản người dùng thường để mở trang báo cáo hoặc URL CSV: phải bị chặn 403. Chưa đăng nhập sẽ được chuyển về đăng nhập.

Minh chứng hữu ích: kết quả 206 test `OK`, trang báo cáo sau khi lọc, file CSV mở với tiếng Việt đúng và lần truy cập bằng tài khoản người dùng thường bị chặn.

## Phạm vi dữ liệu và quyền

| Route | Phương thức | Quyền |
| --- | --- | --- |
| `/dashboard/reports/` | GET/HEAD | Quản trị viên hoặc kỹ thuật viên |
| `/dashboard/reports/export.csv` | GET/HEAD | Cùng quyền với trang báo cáo |

Giữ chính sách của code nền: quản trị viên và kỹ thuật viên được xem báo cáo toàn hệ thống. Đây không phải danh sách cá nhân chỉ chứa ticket được gán cho tài khoản đang đăng nhập. Người dùng thường và tài khoản chỉ có `is_staff` mà không có vai trò phù hợp không được xem/xuất báo cáo.

Các tài khoản từng được gán ticket vẫn xuất hiện trong bộ lọc để xem dữ liệu lịch sử. Việc xuất báo cáo không cấp thêm quyền tải file đính kèm; CSV không chứa nội dung file, đường dẫn lưu trữ hoặc mô tả sự cố.

## Quy ước bộ lọc

| Tham số | Giá trị |
| --- | --- |
| `date_from` | Ngày bắt đầu theo `YYYY-MM-DD`, có thể bỏ trống |
| `date_to` | Ngày kết thúc theo `YYYY-MM-DD`, có thể bỏ trống |
| `category` | `network`, `vpn`, `printer`, `other` |
| `technician` | ID tài khoản có trong danh sách lựa chọn, hoặc `unassigned` |
| `status` | `new`, `in_progress`, `resolved`, `closed` |
| `priority` | `low`, `normal`, `high`, `urgent` |

Ví dụ: `/dashboard/reports/?category=network&technician=unassigned`.

Ngày lọc dựa trên `Ticket.created_at`, tính cả ngày bắt đầu và ngày kết thúc theo múi giờ đang cấu hình của Django. Form hiển thị tên múi giờ. Code nền đang dùng UTC; bản vá không đổi cấu hình này. CSV ghi thời gian ISO 8601 kèm độ lệch múi giờ.

Biểu đồ xu hướng hiển thị cửa sổ 7 ngày, 30 ngày hoặc 6 tháng kết thúc tại ngày Đến ngày nếu được chọn, còn lại kết thúc hôm nay. Nếu chỉ chọn ngày bắt đầu trong tương lai, cửa sổ kết thúc tại ngày bắt đầu đó. Biểu đồ vẫn chịu các bộ lọc còn lại; các thẻ tổng và CSV tính trên toàn khoảng đã lọc, nên khoảng xem biểu đồ có thể ngắn hơn toàn bộ dữ liệu xuất.

Tỷ lệ Đã xử lý hoặc đã đóng tính tổng hai trạng thái `resolved` và `closed` chia cho tổng ticket phù hợp. Các nhóm trạng thái và mức ưu tiên vẫn được hiển thị riêng.

Page và CSV dùng chung form xác thực và cách lọc. CSV đọc dữ liệu tại thời điểm tải, không đóng băng một bản chụp của lần xem trang trước đó. Tham số ngoài danh sách trên không được đưa vào liên kết xuất CSV.

## Triển khai và giới hạn

- `tickets/reporting.py` chứa form lọc, tổng hợp xu hướng, bảng kỹ thuật viên và bộ sinh CSV. `tickets/views.py` dùng các thành phần này cho hai route.
- Tổng hợp xu hướng dùng hai truy vấn theo ngày/tháng thay vì gọi một truy vấn cho mỗi mốc. Số liệu kỹ thuật viên được tổng hợp theo người phụ trách trong một truy vấn.
- CSV đọc theo từng lô, tên file do máy chủ tạo; phản hồi có `Cache-Control: private, no-store` và `nosniff`.
- CSV hướng tới việc xem trong Excel. Những ô có thể được nhận dạng là công thức được thêm ký tự tab trong ô đã đặt dấu nháy. Ký tự này là một phần dữ liệu xuất; khi xử lý CSV bằng chương trình cần lưu ý quy ước đó. Cách xử lý phụ thuộc ứng dụng bảng tính và không bảo đảm cho mọi quy trình lưu/mở lại file.
- Thống kê thời gian giải quyết và cách phân loại từ khóa trên biểu đồ loại sự cố ở Dashboard là các bước phát triển tiếp theo. Bản này tập trung vào bộ lọc và CSV của trang Báo cáo.
- Đã kiểm tra bằng Python 3.13.5, Django 6.1.2 và SQLite. Cần chạy trên môi trường Windows/MySQL của nhóm khi nghiệm thu; chưa kiểm tra trực tiếp bằng Excel trên máy người dùng.

## Kiểm thử

`tickets/test_reports.py` thêm 27 ca, kiểm tra ranh giới ngày/múi giờ, kết hợp bộ lọc, dữ liệu lịch sử, bộ lọc sai, quyền truy cập, CSV tiếng Việt, dấu nháy/xuống dòng, xử lý ô giống công thức, xuất đủ các dòng, thứ tự ổn định, tính chỉ đọc và tổng hợp biểu đồ.

- Toàn bộ 206 test đã đạt trên bản chuẩn bị.
- `manage.py check` đạt.
- `makemigrations --check --dry-run`: không có thay đổi model.

## Commit và push sau khi kiểm tra trên máy bạn

```powershell
git add tickets/reporting.py tickets/test_reports.py tickets/views.py tickets/urls.py templates/tickets/reports.html BACKEND2_REPORTS.md
git diff --cached --stat
git commit -m "feat: filter ticket reports and export CSV"
git push origin backend/lam
```

Commit dự kiến gồm 6 file. File `.patch`, database và file upload giữ ngoài commit. Tạo PR từ `backend/lam` vào `master` khi sẵn sàng ghép vào bản chung.

## Tài liệu tham khảo

- Django CSV/StreamingHttpResponse: https://docs.djangoproject.com/en/6.1/howto/outputting-csv/
- Django TruncDate/TruncMonth: https://docs.djangoproject.com/en/6.1/ref/models/database-functions/
- OWASP CSV Injection: https://owasp.org/www-community/attacks/CSV_Injection
