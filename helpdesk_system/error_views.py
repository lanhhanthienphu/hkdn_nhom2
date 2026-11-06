from django.shortcuts import render


def csrf_failure(request, reason=''):
    # Do not echo CSRF internals or submitted values into the error page.
    return render(request, '403.html', {
        'error_title': 'Phiên làm việc cần được làm mới',
        'error_message': 'Biểu mẫu chưa được gửi. Hãy quay lại trang trước, tải lại trang rồi thử lại. Bạn có thể cần đăng nhập lại nếu phiên đã hết hạn.',
    }, status=403)
