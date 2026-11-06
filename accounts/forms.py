# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator


def style_fields(form):
    for name, field in form.fields.items():
        field.widget.attrs.update({'class': 'form-control'})
        if 'password' in name:
            field.widget.attrs['autocomplete'] = 'new-password'


class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Tên đăng nhập hoặc mật khẩu không đúng. Vui lòng kiểm tra lại.',
        'inactive': 'Tài khoản này chưa được kích hoạt.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['username'].label = 'Tên đăng nhập'
        self.fields['username'].widget.attrs['autocomplete'] = 'username'
        self.fields['password'].label = 'Mật khẩu'
        self.fields['password'].widget.attrs['autocomplete'] = 'current-password'

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        label="Tên đăng nhập",
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={'autocomplete': 'username'}),
        help_text="Tối đa 150 ký tự. Chỉ bao gồm chữ cái, số và các ký tự @/./+/-/_."
    )
    email = forms.EmailField(
        label="Địa chỉ email",
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['email'].widget.attrs['autocomplete'] = 'email'
