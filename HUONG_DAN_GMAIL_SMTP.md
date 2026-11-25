# Gmail SMTP cho Helpdesk

Thiết lập một lần trên mỗi máy Windows chạy Django. Mỗi thành viên có thể dùng Gmail của mình để gửi thư thử. Với website dùng chung, thực hiện cấu hình trên máy chủ chạy Django.

## 1. Tạo mật khẩu ứng dụng

Bật **Xác minh 2 bước** trên tài khoản Gmail dùng để gửi thư. Tạo mật khẩu ứng dụng tên `Helpdesk` và giữ mã 16 ký tự. [Mở trang mật khẩu ứng dụng Google](https://myaccount.google.com/apppasswords)

## 2. Cấu hình một lần trong PowerShell

Nếu server đang chạy, nhấn **Ctrl + C**. Dán toàn bộ khối lệnh vào PowerShell. Nhập địa chỉ Gmail gửi và dán mã ứng dụng khi được hỏi. PowerShell che các ký tự của mã lúc nhập.

```powershell
& {
    $helpdeskGmail = (Read-Host 'Nhap dia chi Gmail gui').Trim()
    $helpdeskAppPassword = Read-Host 'Nhap mat khau ung dung Gmail' -AsSecureString
    $helpdeskPassword = [System.Net.NetworkCredential]::new('', $helpdeskAppPassword).Password -replace '\s', ''
    if (-not $helpdeskGmail -or $helpdeskPassword.Length -ne 16) {
        throw 'Can nhap dia chi Gmail va mat khau ung dung 16 ky tu.'
    }

    $helpdeskSender = [System.Net.Mail.MailAddress]::new($helpdeskGmail, 'dịch vụ helpdesk')
    [Environment]::SetEnvironmentVariable('HELPDESK_SMTP_USER', $helpdeskSender.Address, 'User')
    [Environment]::SetEnvironmentVariable('HELPDESK_SMTP_PASSWORD', $helpdeskPassword, 'User')
    [Environment]::SetEnvironmentVariable('HELPDESK_FROM_EMAIL', $helpdeskSender.ToString(), 'User')
    [Environment]::SetEnvironmentVariable('HELPDESK_EMAIL_MODE', 'smtp', 'User')
    Write-Host 'Da luu cau hinh Gmail SMTP.'
}
```

Windows lưu các biến này trong Registry của tài khoản đang dùng. Giữ mật khẩu ứng dụng trên máy chạy Django và ngoài GitHub. [Tài liệu Microsoft](https://learn.microsoft.com/en-us/dotnet/api/system.environment.setenvironmentvariable)

## 3. Mở lại VS Code và chạy Helpdesk

Đóng hết cửa sổ VS Code rồi mở lại từ menu Start. Trong thư mục có `manage.py`, chạy lệnh dưới đây mỗi khi cần mở server.

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Tạo một ticket thử rồi phân công cho kỹ thuật viên có **địa chỉ email** trong tài khoản Helpdesk. Thư **Được phân công xử lý** sẽ gửi tới địa chỉ đó. Nếu thư xuất hiện trong Terminal, kiểm tra `$env:HELPDESK_EMAIL_MODE` trong tab đang dùng để chạy server. Giá trị cần là `smtp`.

