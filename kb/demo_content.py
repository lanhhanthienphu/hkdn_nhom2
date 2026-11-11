"""Demo articles with recognizable titles; the seed command never edits existing ones."""

DEMO_ARTICLES = [
    {
        "title": "[Mẫu] Kiểm tra khi máy tính không kết nối được Wi-Fi",
        "content": (
            "Dấu hiệu: Máy tính không kết nối được mạng Wi-Fi của phòng học.\n\n"
            "1. Kiểm tra Wi-Fi đã bật và chế độ máy bay đã tắt.\n"
            "2. Chọn đúng tên mạng do đơn vị cung cấp.\n"
            "3. Thử ngắt kết nối và kết nối lại khi không có tác vụ quan trọng.\n"
            "4. Ghi lại tên mạng, phòng học, thời điểm và thông báo lỗi.\n\n"
            "Nếu vẫn lỗi, gửi ticket để bộ phận kỹ thuật kiểm tra. Không ghi mật khẩu vào ticket."
        ),
    },
    {
        "title": "[Mẫu] Kiểm tra khi máy tính không nhận mạng LAN",
        "content": (
            "Dấu hiệu: Máy đã cắm dây mạng nhưng không truy cập được hệ thống.\n\n"
            "1. Kiểm tra đầu cáp được cắm chắc vào máy và ổ mạng.\n"
            "2. Quan sát đèn báo tại cổng mạng nếu thiết bị có đèn.\n"
            "3. Xác định sự cố chỉ xảy ra ở một máy hay nhiều máy trong phòng.\n"
            "4. Ghi lại vị trí ổ mạng, tên thiết bị và thời điểm xảy ra lỗi.\n\n"
            "Gửi ticket nếu vẫn không kết nối được. Việc cấu hình thiết bị mạng do kỹ thuật viên thực hiện."
        ),
    },
    {
        "title": "[Mẫu] Kiểm tra khi Wi-Fi chậm hoặc chập chờn",
        "content": (
            "Dấu hiệu: Trang web tải lâu, cuộc họp bị giật hoặc kết nối hay ngắt.\n\n"
            "1. Kiểm tra máy đang chọn đúng mạng Wi-Fi.\n"
            "2. Tạm dừng các tác vụ tải dữ liệu lớn không cần thiết.\n"
            "3. Ghi lại vị trí, khoảng thời gian lỗi và số người cùng gặp sự cố.\n"
            "4. Xác định một ứng dụng bị chậm hay tất cả ứng dụng đều bị ảnh hưởng.\n\n"
            "Đính kèm thông báo lỗi hoặc ảnh minh họa khi gửi ticket."
        ),
    },
    {
        "title": "[Mẫu] Kiểm tra khi không kết nối được VPN",
        "content": (
            "Dấu hiệu: Ứng dụng VPN không kết nối được hoặc báo lỗi đăng nhập.\n\n"
            "1. Kiểm tra máy có truy cập Internet bình thường.\n"
            "2. Kiểm tra ngày giờ của thiết bị.\n"
            "3. Chọn đúng cấu hình VPN đã được bộ phận kỹ thuật cung cấp.\n"
            "4. Ghi lại mã lỗi và thời điểm thử kết nối.\n\n"
            "Gửi ticket khi cần hỗ trợ. Không gửi mật khẩu hoặc mã xác thực."
        ),
    },
    {
        "title": "[Mẫu] Kiểm tra khi máy in mạng không nhận lệnh in",
        "content": (
            "Dấu hiệu: Đã gửi lệnh nhưng máy in không hoạt động hoặc báo ngoại tuyến.\n\n"
            "1. Kiểm tra máy in đã bật và có thông báo thiếu giấy, kẹt giấy hay không.\n"
            "2. Kiểm tra đã chọn đúng tên máy in của đơn vị.\n"
            "3. Kiểm tra máy tính đang kết nối mạng phù hợp.\n"
            "4. Ghi lại tên máy in, phòng đặt máy và thông báo lỗi.\n\n"
            "Gửi ticket nếu chưa xử lý được. Không xóa lệnh in của người khác."
        ),
    },
    {
        "title": "[Mẫu] Kiểm tra khi không truy cập được website nội bộ",
        "content": (
            "Dấu hiệu: Trình duyệt không mở được cổng thông tin nội bộ.\n\n"
            "1. Kiểm tra địa chỉ website đúng theo hướng dẫn của đơn vị.\n"
            "2. Kiểm tra máy đang kết nối mạng nội bộ hoặc VPN nếu được yêu cầu.\n"
            "3. Ghi lại thông báo lỗi và thời điểm không truy cập được.\n"
            "4. Xác định các website khác có truy cập được hay không.\n\n"
            "Gửi ticket kèm địa chỉ website và ảnh thông báo lỗi để kỹ thuật viên kiểm tra."
        ),
    },
    {
        "title": "[Mẫu] Kiểm tra khi không mở được thư mục dùng chung",
        "content": (
            "Dấu hiệu: Không mở được thư mục mạng hoặc xuất hiện thông báo thiếu quyền.\n\n"
            "1. Kiểm tra máy đang ở mạng nội bộ hoặc kết nối VPN theo yêu cầu.\n"
            "2. Kiểm tra đường dẫn thư mục theo thông tin được cấp.\n"
            "3. Xác định đã từng truy cập được hay đây là lần sử dụng đầu tiên.\n"
            "4. Ghi lại đường dẫn, tên tài khoản và nội dung thông báo lỗi.\n\n"
            "Gửi ticket để kỹ thuật viên kiểm tra kết nối hoặc quyền được cấp."
        ),
    },
]
