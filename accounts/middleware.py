# accounts/middleware.py
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.urls import reverse, NoReverseMatch

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Danh sách các đường dẫn công khai (không cần đăng nhập)
        self.exempt_urls = [
            '/accounts/login/',
            '/accounts/register/',
        ]

    def __call__(self, request):
        path = request.path

        # Bỏ qua kiểm tra cho các file tĩnh (CSS, JS, hình ảnh)
        if path.startswith('/static/') or path.startswith('/media/'):
            return self.get_response(request)

        # Nếu người dùng chưa đăng nhập và trang hiện tại không nằm trong danh sách miễn trừ
        if not request.user.is_authenticated and path not in self.exempt_urls:
            if request.path_info.startswith('/api/kb/'):
                response = JsonResponse({
                    'error': 'authentication_required',
                    'message': 'Vui lòng đăng nhập để xem kho kiến thức.',
                }, status=401, json_dumps_params={'ensure_ascii': False})
                response['Cache-Control'] = 'no-store'
                return response

            try:
                login_url = reverse('accounts:login')
            except NoReverseMatch:
                login_url = '/accounts/login/'
            
            # Chuyển hướng về trang đăng nhập kèm theo tham số 'next'
            # Keep query parameters (e.g. location from a classroom QR link).
            return redirect_to_login(request.get_full_path(), login_url)

        response = self.get_response(request)
        return response
