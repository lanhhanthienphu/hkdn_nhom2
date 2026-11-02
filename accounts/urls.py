# accounts/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import register_view

app_name = 'accounts'

urlpatterns = [
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('register/', register_view, name='register'),
]