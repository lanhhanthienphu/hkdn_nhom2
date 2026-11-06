from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm

@never_cache
@require_http_methods(['GET', 'POST'])
def register_view(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = ''
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Tự động đăng nhập luôn sau khi đăng ký thành công
            return redirect(next_url or 'tickets:home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})
