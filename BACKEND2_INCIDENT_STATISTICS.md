# Backend 2 — Chuẩn hóa thống kê nhóm sự cố

Bản vá `backend2-incident-statistics.patch` áp dụng trên nền `master` tại `4618c3e738cbc97bc67160ed07ed1eb407790541`, sau PR #20 thời gian giải quyết lần đầu. Nền trước bản này có 233 test.

## Vấn đề và cách sửa

Biểu đồ Dashboard cũ đếm riêng các từ khóa trong tiêu đề/mô tả. Một ticket có Internet, Wi-Fi và router có thể xuất hiện ở ba nhóm, làm tổng các cột vượt tổng số ticket. Chuỗi `ap` trong Laptop cũng có thể bị nhận dạng nhầm là lỗi Wi-Fi/access point. Dashboard và Báo cáo dùng hai cách phân nhóm khác nhau.

Bản sửa thống kê theo `Ticket.category` đã lưu. Mỗi ticket được tính một lần vào một nhóm:

| Giá trị | Nhãn |
| --- | --- |
| `network` | Mạng LAN / Wi-Fi |
| `vpn` | Kết nối VPN |
| `printer` | Máy in |
| `other` | Sự cố khác |

Nhóm trống hoặc giá trị ngoài lựa chọn hiện tại được gom thành **Chưa xác định**. Nhóm này chỉ xuất hiện khi có dữ liệu tương ứng, tách riêng khỏi nhóm Sự cố khác. Không tự sửa hoặc xóa dữ liệu ticket cũ.

Dashboard và Báo cáo dùng chung cách tính, thứ tự nhóm và màu biểu đồ. Tổng số trong biểu đồ bằng tổng ticket của tập dữ liệu đang thống kê. Nếu queryset có join tới nhiều dòng lịch sử/file, một ticket vẫn chỉ được tính một lần.

Phân loại hiện có phản ánh nhóm người dùng/quản trị đã chọn. Muốn thống kê chi tiết riêng Internet, Wi-Fi, LAN, thiết bị mạng hoặc máy chủ, cần thiết kế trường loại sự cố tương ứng để thu thập dữ liệu rõ ràng với BE1.

## Áp dụng trên Windows

1. Save All trong VS Code, rồi đóng các tab `tickets/views.py`, `templates/tickets/admin_dashboard.html`, `templates/tickets/reports.html` trước khi áp dụng để tránh ghi đè bằng nội dung tab cũ.
2. Đặt `backend2-incident-statistics.patch` cạnh `manage.py`.
3. Kiểm tra trạng thái:

```powershell
git status
```

Tiếp tục trên nhánh `backend/lam`. Nếu chỉ còn các file `.patch` chưa được theo dõi, có thể áp dụng. Nếu có code đang sửa dở, giữ lại các thay đổi đó trước khi áp dụng.

4. Kiểm tra patch:

```powershell
git apply --check .\backend2-incident-statistics.patch
```

Thành công thường không in gì. Nếu có lỗi thì dừng ở đây và đối chiếu phiên bản code; không áp dụng lại những bản vá cũ, dùng `--reject` hoặc chép đè file đang sửa.

5. Áp dụng và chạy kiểm tra:

```powershell
git apply .\backend2-incident-statistics.patch
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test kb accounts tickets notifications
```

Trên nền đã nêu, bộ kiểm thử dự kiến có 249 ca. Chỉ tiếp tục khi kết quả `OK`. Bản này không thêm thư viện hoặc migration.

6. Chạy server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

7. Đăng nhập quản trị viên và mở `http://127.0.0.1:8000/dashboard/admin/`.

## Kiểm tra trực tiếp và lấy minh chứng

1. Trên Dashboard, tìm biểu đồ **Thống kê theo nhóm sự cố**. Chú thích phải ghi mỗi ticket được tính một lần. Các nhãn chính là LAN/Wi-Fi, VPN, Máy in và Sự cố khác.
2. Ghi lại tổng ticket và số của nhóm LAN/Wi-Fi. Mở `/tickets/new/`, tạo một ticket:
   - Tiêu đề: Internet Wi-Fi router tại A.201.
   - Nhóm sự cố: Mạng LAN / Wi-Fi.
   - Vị trí: A.201.
   - Mô tả: Wi-Fi chập chờn, không vào được Internet qua router của phòng A.201.
3. Tải lại Dashboard. Tổng ticket tăng 1 và nhóm LAN/Wi-Fi tăng 1. Các từ khóa Internet/router trong cùng ticket không làm tăng các nhóm khác.
4. Mở `/dashboard/reports/`, bấm Xóa bộ lọc. Biểu đồ cơ cấu nhóm phải khớp Dashboard khi cùng xem toàn bộ dữ liệu.
5. Trong Báo cáo, chọn nhóm LAN/Wi-Fi rồi Áp dụng bộ lọc. Biểu đồ chỉ có số ở nhóm này; xuất CSV và đối chiếu số dòng dữ liệu với tổng ticket phù hợp. CSV vẫn có 11 cột, bao gồm hai cột thời gian giải quyết lần đầu.
6. Nếu xuất hiện Chưa xác định, xem dữ liệu nhóm trên các ticket liên quan. Đây là nhắc kiểm tra dữ liệu cũ, không phải ticket tự được phân loại thành Sự cố khác.

Để xem danh sách nhóm không hợp lệ bằng lệnh chỉ đọc, có thể dùng:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from tickets.models import Ticket; print(list(Ticket.objects.exclude(category__in=[key for key, label in Ticket.CATEGORY_CHOICES]).values('id', 'title', 'category')))"
```

Không cần tạo nhóm sai trong database chỉ để chụp minh chứng; các trường hợp dữ liệu cũ/nhóm trống đã có kiểm thử tự động.

## Phạm vi số liệu

- Biểu đồ Dashboard là tổng quan toàn hệ thống như thiết kế hiện tại. Bộ lọc ở bảng danh sách trên Dashboard áp dụng cho danh sách đó.
- Biểu đồ Báo cáo dùng tập ticket đã qua bộ lọc ngày tạo, nhóm, người phụ trách, trạng thái và ưu tiên. CSV dùng cùng bộ lọc.
- Không so sánh biểu đồ Dashboard toàn hệ thống với Báo cáo đang lọc một tập con. Xóa bộ lọc ở Báo cáo để đối chiếu toàn bộ.
- Nhãn Chưa xác định chỉ có ý nghĩa dữ liệu nằm ngoài nhóm đã định nghĩa. CSV giữ nguyên giá trị nhóm của bản ghi để có thể kiểm tra dữ liệu gốc.
- Chính sách truy cập tiếp tục theo các trang hiện có: Dashboard quản trị dành cho quản trị viên; Báo cáo dành cho quản trị viên/kỹ thuật viên. Người dùng thường không xem được báo cáo toàn hệ thống.

## Điểm tích hợp và kiểm thử

- `get_category_stats()` dùng một truy vấn nhóm theo category và đếm PK duy nhất; thứ tự nhóm dựa vào `Ticket.CATEGORY_CHOICES`.
- `get_category_chart_data()` cung cấp labels/data/colors chung cho hai biểu đồ và cờ nhắc dữ liệu chưa xác định.
- Tên hàm cũ `get_network_incident_types_stats()` được giữ làm đầu vào tương thích, trả thống kê theo nhóm đã lưu.
- `tickets/test_incident_statistics.py` thêm 16 test cho ticket nhiều từ khóa, Laptop/AP, phạm vi queryset, dữ liệu cũ, nhóm trống, đếm trùng do join, nhóm/màu ổn định, Dashboard, bộ lọc Báo cáo, CSV và số truy vấn.
- Kiểm thử dùng Python 3.13.5, Django 6.1.2, SQLite; cần chạy lại trên môi trường của nhóm khi nghiệm thu.
- Đã chạy toàn bộ **249 test — OK**. `manage.py check` đạt; `makemigrations --check --dry-run` không có thay đổi model.

Minh chứng báo cáo: kết quả test OK, biểu đồ Dashboard có tổng khớp số ticket, trường hợp thêm một ticket nhiều từ khóa chỉ tăng một nhóm, và Báo cáo/CSV cùng bộ lọc khớp nhau.

## Commit và push khi kiểm tra xong

```powershell
git add tickets/views.py tickets/test_incident_statistics.py
git add templates/tickets/admin_dashboard.html templates/tickets/reports.html
git add BACKEND2_REPORTS.md BACKEND2_INCIDENT_STATISTICS.md
git diff --cached --stat
```

Danh sách dự kiến gồm 6 file. Sau khi xem lại:

```powershell
git commit -m "fix: sửa thống kê nhóm sự cố và tránh đếm trùng ticket"
git push origin backend/lam
```

Giữ các file `.patch`, database và file upload ngoài commit. Tạo PR từ `backend/lam` vào `master` khi sẵn sàng ghép vào bản chung.
