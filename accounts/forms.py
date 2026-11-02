# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label="Tên đăng nhập",
        help_text="Tối đa 150 ký tự. Chỉ bao gồm chữ cái, số và các ký tự @/./+/-/_."
    )
    email = forms.EmailField(
        label="Địa chỉ email",
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email']