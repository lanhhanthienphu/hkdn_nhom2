# Backend 1 — Bàn giao Cơ sở dữ liệu và Luồng xử lý Ticket (Gia Bảo)

Tài liệu này tổng hợp toàn bộ các models, luồng xử lý CRUD, phân công sự cố và quyền hạn đã được hiện thực hóa theo đúng đề tài và sơ đồ thiết kế.

---

## 1. Cơ sở dữ liệu & Models

### App `accounts` ([`accounts/models.py`](file:///d:/hkdn_nhom2/accounts/models.py))
- **`Role` (bảng `roles`)**:
  - `id`: Khóa chính
  - `name`: Tên vai trò (`admin`, `technician`, `user`) - `unique=True`
  - `description`: Mô tả vai trò
- **`UserProfile` (bảng `user_profiles`)**:
  - `user`: Liên kết 1-1 với `auth_user` (`OneToOneField`)
  - `role`: Khóa ngoại trỏ đến `Role` (`ForeignKey`)
  - `phone`: Số điện thoại
  - `department`: Phòng ban / Vị trí làm việc
  - Các phương thức kiểm tra quyền:
    - `is_admin()`: Trả về `True` nếu là Superuser hoặc vai trò Admin.
    - `is_technician()`: Trả về `True` nếu là Kỹ thuật viên (hoặc Admin).
    - `is_end_user()`: Trả về `True` nếu là Người dùng cuối thông thường.
  - Tự động gán: Khi tạo user mới (qua form đăng ký hoặc code), Signal tự động tạo `UserProfile` với vai trò `user`.

### App `tickets` ([`tickets/models.py`](file:///d:/hkdn_nhom2/tickets/models.py))
- **`Ticket` (bảng `tickets`)**:
  - `id`: Khóa chính (Mã ticket dạng `HD-{id}`)
  - `title`: Tiêu đề sự cố (chuỗi tối đa 150 ký tự)
  - `category`: Nhóm sự cố (`network`, `vpn`, `printer`, `other`)
  - `priority`: Mức độ ưu tiên (`low`, `normal`, `high`, `urgent`)
  - `location`: Vị trí / Phòng xảy ra sự cố
  - `description`: Mô tả chi tiết sự cố
  - `status`: Trạng thái (`new`: Chờ tiếp nhận, `in_progress`: Đang xử lý, `resolved`: Đã xử lý, `closed`: Đã đóng)
  - `created_by`: Người gửi ticket (`ForeignKey(User)`)
  - `assigned_to`: Kỹ thuật viên phụ trách (`ForeignKey(User)`, có thể để trống)
  - `created_at` / `updated_at`: Thời gian tạo và cập nhật
  - `attachment_name` / `attachment_size`: Metadata file đính kèm
  - Các hàm nghiệp vụ & thuộc tính:
    - `get_code()` / `.code`: Trả về mã chuỗi dạng `HD-1001`.
    - `can_view(user)`: Kiểm tra quyền xem ticket (Admin/Kỹ thuật viên, Người tạo hoặc Người được gán).
    - `assign_technician(tech, by, note="")`: Gán kỹ thuật viên phụ trách, tự chuyển trạng thái sang `in_progress` nếu đang `new`, đồng thời tự động ghi 1 dòng vào `TicketHistory`.
    - `change_status(new_status, by, note="")`: Đổi trạng thái ticket và tự động ghi 1 dòng vào `TicketHistory`.
    - `.category_label`, `.priority_label`, `.status_label`, `.steps`: Cung cấp nhãn tiếng Việt và tiến độ từng bước cho giao diện.
- **`Comment` (bảng `comments`)**:
  - `ticket`: Khóa ngoại tới `Ticket`
  - `user`: Khóa ngoại tới `User`
  - `content`: Nội dung trao đổi
  - `created_at`: Thời gian bình luận
- **`TicketHistory` (bảng `ticket_history`)**:
  - `ticket`: Khóa ngoại tới `Ticket`
  - `changed_by`: Người thực hiện thay đổi
  - `old_status`: Trạng thái cũ
  - `new_status`: Trạng thái mới
  - `assigned_to`: Kỹ thuật viên được gán
  - `note`: Ghi chú thay đổi
  - `created_at`: Thời gian ghi nhận

---

## 2. Các Endpoint & Views ([`tickets/views.py`](file:///d:/hkdn_nhom2/tickets/views.py))

| Phương thức | URL | Tên Route | Mô tả |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | `tickets:home` | Trang chủ cá nhân: Thống kê số lượng ticket thật theo trạng thái, hiển thị 3 ticket gần đây của user, các bài hướng dẫn KB |
| `GET` | `/tickets/` | `tickets:list` | Danh sách ticket: Phân quyền (User chỉ thấy ticket của mình; Kỹ thuật viên/Admin thấy toàn bộ), tìm kiếm theo từ khóa/mã HD-*, lọc trạng thái/nhóm/độ ưu tiên, sắp xếp và phân trang 5 ticket/trang |
| `GET, POST` | `/tickets/new/` | `tickets:create` | Tạo ticket mới: Validate dữ liệu, lưu vào database, tạo lịch sử ban đầu |
| `GET, POST` | `/tickets/<id>/` | `tickets:detail` | Chi tiết ticket: Hiển thị đầy đủ thông tin, tiến độ, bình luận, lịch sử. Cho phép gửi bình luận (chặn gửi khi ticket đã đóng) |
| `POST` | `/tickets/<id>/assign/` | `tickets:assign` | Phân công kỹ thuật viên phụ trách (dành cho Admin / Kỹ thuật viên), nhận `technician_id` và `note` |
| `POST` | `/tickets/<id>/status/` | `tickets:change_status` | Cập nhật trạng thái sự cố (dành cho Admin / Kỹ thuật viên, hoặc Người tạo đóng ticket của mình), nhận `status` và `note` |

---

## 3. Quản trị Django Admin ([`/admin/`](http://127.0.0.1:8000/admin/))
- Đã đăng ký đầy đủ các Model:
  - `RoleAdmin`, `UserProfileAdmin` (tích hợp Inline trong User)
  - `TicketAdmin` (tích hợp xem nhanh Comments và Lịch sử TicketHistory ngay bên trong trang chi tiết Ticket)
  - `CommentAdmin`, `TicketHistoryAdmin`

---

## 4. Bàn giao cho các thành viên
1. **Frontend 1 (Minh Khôi)**:
   - Toàn bộ giao diện đã tự động nối với database thật.
   - Nhãn "Bản xem thử" đã được tắt ở chế độ thật.
2. **Backend 2 (Trường Lâm)**:
   - Model `Ticket` đã sẵn sàng tại `tickets.models.Ticket`.
   - Lâm có thể tạo model `Attachment` liên kết `ForeignKey('tickets.Ticket')` để hoàn tất upload/tải file vật lý và kích hoạt gửi email thông báo khi `Ticket` hoặc `TicketHistory` được tạo.
3. **Frontend 2 (Minh Khang)**:
   - Dùng các route `/tickets/`, `/tickets/<id>/assign/`, `/tickets/<id>/status/` để tích hợp vào Dashboard quản trị và màn hình phân công kỹ thuật viên.

---

## 5. Kết quả kiểm thử
- Chạy toàn bộ test suite dự án:
  ```powershell
  python manage.py test
  ```
  **Kết quả:** 84/84 tests PASS (0 lỗi, 0 cảnh báo).

