# Backend 2 — Thời gian giải quyết lần đầu

Bản vá `backend2-resolution-metrics.patch` áp dụng sau phần lọc báo cáo/CSV đã merge ở PR #19, trên nền `master` tại `4c80fe29bb2c8429e2f58fef90c6c23f42c6ba47` (206 test).

## Kết quả

- Trang `/dashboard/reports/` có thời gian giải quyết trung bình, số ticket đủ dữ liệu, chưa giải quyết và chưa đủ dữ liệu.
- Có bảng chi tiết ngày tạo, ngày giải quyết lần đầu và thời gian giải quyết; phân trang 10 ticket mỗi trang.
- CSV có thêm 2 cột ở cuối, giữ vị trí 9 cột ban đầu: Ngày giải quyết lần đầu (ISO 8601) và Thời gian giải quyết lần đầu (phút).
- Các số liệu tiếp tục dùng cùng bộ lọc ngày tạo, nhóm, người phụ trách, trạng thái và mức ưu tiên.
- Tính từ `TicketHistory` đã có; không thêm field, migration, thư viện hoặc sửa dữ liệu lịch sử.

## Quy ước tính

Thời gian giải quyết lần đầu = thời điểm chuyển sang `resolved` lần đầu có đủ bằng chứng trong lịch sử − `Ticket.created_at`.

Đây là thời gian theo lịch, có cả thời gian chờ và thời gian ngoài giờ làm việc. Không phải số giờ kỹ thuật viên trực tiếp thao tác, thời gian theo ca hoặc chỉ số SLA có lịch làm việc riêng.

Một mốc hợp lệ phải có trạng thái cũ là `new`, `in_progress` hoặc `closed`, trạng thái mới là `resolved`, và thời điểm không trước ngày tạo ticket. Bản ghi phân công giữ nguyên `resolved -> resolved` hoặc tạo sẵn ticket ở trạng thái `resolved` với trạng thái cũ rỗng không được xem là một lần chuyển trạng thái giải quyết.

Nếu đã có bằng chứng ticket ở trạng thái resolved sớm hơn mốc chuyển hợp lệ còn lại, dữ liệu được xếp Chưa đủ dữ liệu; không lấy lần giải quyết sau để thay cho lần đầu bị thiếu. Mốc đầu sai thời gian cũng không được thay bằng mốc sau. Phép tính phản ánh lịch sử hiện có, không khôi phục các sự kiện đã bị xóa.

| Trường hợp | Hiển thị | Tính trung bình |
| --- | --- | --- |
| Có lần giải quyết đầu đủ dữ liệu | Thời gian tương ứng | Có |
| Có lần giải quyết đủ dữ liệu, sau đó đã mở lại | Vẫn giữ lần đầu | Có |
| Trạng thái mới/đang xử lý, không có bằng chứng từng giải quyết | Chưa giải quyết | Không |
| Đã xử lý/đã đóng nhưng thiếu mốc hợp lệ | Chưa đủ dữ liệu | Không |
| Lịch sử cho thấy đã giải quyết nhưng thiếu mốc đầu hoặc thời gian sai | Chưa đủ dữ liệu | Không |
| Giải quyết đúng thời điểm tạo | 0 giây | Có, là giá trị 0 thật |

Ví dụ có hai ticket giải quyết sau 20 và 40 phút, một ticket chưa giải quyết và một ticket cũ thiếu lịch sử: trung bình là **30 phút trên 2 ticket đủ dữ liệu**.

Bộ lọc ngày vẫn dựa trên ngày tạo ticket. Ticket tạo trong khoảng đã chọn có thể được giải quyết ngoài khoảng đó và vẫn được tính vào tập báo cáo. Người phụ trách trong bảng/CSV là người hiện đang được gán, không mặc định là người đã thực hiện lần giải quyết đầu tiên.

## Áp dụng trên Windows

1. Trong VS Code, Save All rồi đóng các tab `tickets/reporting.py`, `tickets/views.py`, `tickets/test_reports.py` và `templates/tickets/reports.html` trước khi áp dụng, tránh lưu nội dung tab cũ đè lên file vừa được patch cập nhật.
2. Đặt `backend2-resolution-metrics.patch` cạnh `manage.py`.
3. Kiểm tra đang ở nhánh `backend/lam`:

```powershell
git status
```

Nếu chỉ còn các file `.patch` chưa được theo dõi, có thể tiếp tục. Nếu đang có code sửa dở, giữ riêng các thay đổi trước khi áp dụng.

4. Kiểm tra patch:

```powershell
git apply --check .\backend2-resolution-metrics.patch
```

Thành công thường không in gì. Nếu báo lỗi thì dừng ở bước này và đối chiếu phiên bản; không dùng `--reject` hoặc chép đè file đang sửa.

5. Áp dụng rồi kiểm tra:

```powershell
git apply .\backend2-resolution-metrics.patch
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test kb accounts tickets notifications
```

Bộ kiểm thử dự kiến có 233 ca trên nền đã nêu. Chỉ tiếp tục khi kết quả `OK`. Bản này không cần chạy `makemigrations` hoặc cài thêm thư viện.

6. Chạy server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

7. Đăng nhập tài khoản quản trị viên hoặc kỹ thuật viên, mở `http://127.0.0.1:8000/dashboard/reports/`.

## Kiểm tra trực tiếp

1. Mở trang Báo cáo, xem phần Thời gian giải quyết lần đầu. Nếu các ticket cũ chưa có lịch sử đầy đủ, chúng được hiển thị Chưa đủ dữ liệu và chưa tạo ra số trung bình giả.
2. Mở `/tickets/new/`, tạo một ticket có tên dễ nhận biết, ví dụ Kiểm tra thống kê thời gian Wi-Fi. Sau khi tạo, ghi lại mã HD và thời điểm tạo trên trang chi tiết.
3. Dùng luồng quản lý hoặc Admin để phân công ticket, sau đó đổi trạng thái thành Đã xử lý và lưu. Việc đổi trạng thái này tạo lịch sử để tính thời gian.
4. Quay lại Báo cáo, chọn khoảng ngày có ngày tạo ticket và bộ lọc phù hợp. Bảng chi tiết phải hiện ngày giải quyết đầu và khoảng thời gian từ lúc tạo; số trung bình tính trên các ticket đủ dữ liệu trong cùng bộ lọc.
5. Mở lại ticket bằng cách chuyển về Đang xử lý, rồi giải quyết lần nữa. Ngày giải quyết đầu và thời gian lần đầu phải giữ nguyên.
6. Bấm Xuất CSV. File có 11 cột, hai cột cuối chứa mốc giải quyết và số phút. Ticket chưa giải quyết hoặc thiếu dữ liệu để trống hai ô này; giá trị `0.00` chỉ dành cho thời gian hợp lệ được làm tròn về 0 phút.
7. Chuyển trang của bảng chi tiết: số trung bình vẫn dựa trên toàn tập ticket đã lọc, CSV vẫn xuất toàn bộ tập đó. Bộ lọc được giữ khi chuyển trang.
8. Kiểm tra bằng người dùng thường: trang báo cáo và xuất CSV vẫn trả 403. Chưa đăng nhập được chuyển về đăng nhập.

Không cần sửa lùi ngày tạo hoặc ngày lịch sử để thử trên database đang dùng. Các trường hợp có thời gian cố định 20/40 phút, thiếu lịch sử, mở lại và mốc sai đã có trong kiểm thử tự động.

## Đọc số liệu và CSV

- Giao diện làm tròn thời gian đến giây và hiển thị ngày/giờ/phút/giây. CSV ghi số phút với 2 chữ số thập phân; chênh lệch rất nhỏ do làm tròn đơn vị là bình thường.
- Mốc CSV dùng ISO 8601 có độ lệch múi giờ. Trang báo cáo dùng múi giờ cấu hình sẵn và hiển thị tên múi giờ; bản này không đổi `TIME_ZONE`.
- Trung bình bỏ qua ticket chưa đo được, không coi chúng là 0. Ticket đã từng giải quyết rồi mở lại vẫn được tính vì chỉ số này đo lần đầu, không phải số lượng đang ở trạng thái resolved.
- CSV không thêm cột trạng thái chất lượng dữ liệu; bảng trên trang phân biệt Chưa giải quyết và Chưa đủ dữ liệu. Hai trường hợp đều có hai ô đo thời gian trống trong CSV.
- Chính sách truy cập giữ như báo cáo hiện có: quản trị viên và kỹ thuật viên xem báo cáo toàn hệ thống; tài khoản chỉ có `is_staff` nhưng không có vai trò phù hợp không được xem.
- Các giá trị được đọc tại lúc xem/tải và có thể thay đổi nếu lịch sử hoặc ticket được cập nhật giữa hai lần yêu cầu. Chưa có cơ chế lưu bản chụp báo cáo hay khôi phục lịch sử thiếu.

## Điểm tích hợp

- `tickets/resolution_metrics.py`: chọn mốc từ lịch sử, phân loại chất lượng dữ liệu, tính tổng hợp và định dạng thời gian.
- `tickets/views.py`: bổ sung số tổng hợp và bảng chi tiết có phân trang cho report context.
- `tickets/reporting.py`: thêm hai cột CSV từ cùng phép tính.
- Truy vấn dùng ORM/Subquery; không truy vấn lịch sử riêng từng ticket và không nhân số ticket khi có nhiều dòng lịch sử.

## Kiểm thử và minh chứng

- `tickets/test_resolution_metrics.py` thêm 27 test cho mốc đầu, mở lại/đóng lại, nhật ký phân công, thiếu lịch sử, thời gian sai, giá trị 0, trung bình, bộ lọc, phân trang, CSV, múi giờ, escape HTML, hiệu năng truy vấn và luồng tạo/phân công/giải quyết thực tế.
- `tickets/test_reports.py` cập nhật số cột CSV từ 9 sang 11; các kiểm tra bộ lọc, quyền và an toàn CSV tiếp tục chạy.
- Đã chạy toàn bộ **233 test — OK**; `manage.py check` đạt, `makemigrations --check --dry-run` không có thay đổi model.
- Môi trường kiểm tra: Python 3.13.5, Django 6.1.2, SQLite. Cần chạy lại trên máy Windows và môi trường database của nhóm.
- Minh chứng: kết quả test OK, trang báo cáo có số trung bình và bảng thời gian, file CSV có 11 cột, và số liệu giữ nguyên sau khi mở lại/giải quyết lại cùng ticket.

## Commit sau khi kiểm tra

```powershell
git add tickets/resolution_metrics.py tickets/reporting.py tickets/views.py
git add tickets/test_resolution_metrics.py tickets/test_reports.py templates/tickets/reports.html
git add BACKEND2_REPORTS.md BACKEND2_RESOLUTION_METRICS.md
git diff --cached --stat
git commit -m "feat: report first ticket resolution times"
```

Commit dự kiến gồm 8 file. Khi muốn đưa commit lên nhánh riêng:

```powershell
git push origin backend/lam
```

Các file `.patch`, database và file upload không đưa vào commit. Tạo PR từ `backend/lam` vào `master` khi sẵn sàng ghép vào bản chung.

## Tài liệu tham khảo

- Django Subquery, biểu thức và DurationField: https://docs.djangoproject.com/en/6.1/ref/models/expressions/
- Django Avg và aggregate: https://docs.djangoproject.com/en/6.1/ref/models/querysets/#avg
