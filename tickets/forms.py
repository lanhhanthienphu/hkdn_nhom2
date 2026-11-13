from django import forms

from .attachment_validators import (
    ATTACHMENT_EXTENSIONS,
    MAX_ATTACHMENT_BYTES,
    validate_attachment,
)
from .models import Ticket


class TicketForm(forms.Form):
    title = forms.CharField(
        label='Tiêu đề sự cố', min_length=5, max_length=150,
        help_text='Mô tả ngắn gọn vấn đề bạn gặp (5–150 ký tự).',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: Không kết nối được Wi-Fi tại phòng A.201'}))
    category = forms.ChoiceField(
        label='Nhóm sự cố', choices=[('', 'Chọn nhóm sự cố')] + Ticket.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}))
    priority = forms.ChoiceField(
        label='Độ ưu tiên', choices=Ticket.PRIORITY_CHOICES, initial='normal',
        help_text='Chọn Khẩn cấp khi sự cố làm gián đoạn hoạt động của nhiều người.',
        widget=forms.Select(attrs={'class': 'form-select'}))
    location = forms.CharField(
        label='Phòng / vị trí xảy ra sự cố', max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: Tòa A, phòng A.201'}))
    description = forms.CharField(
        label='Mô tả chi tiết', min_length=20, max_length=5000,
        help_text='Nêu thời điểm xảy ra lỗi, thiết bị, mức độ ảnh hưởng và những cách bạn đã thử (ít nhất 20 ký tự).',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'data-character-count': '',
                                    'placeholder': 'Sự cố bắt đầu khi nào? Bạn nhìn thấy thông báo lỗi gì?'}))
    attachment = forms.FileField(
        label='File đính kèm', required=False,
        help_text='Chọn 1 file JPG, PNG, PDF, TXT hoặc LOG; tối đa 10 MB.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.pdf,.txt,.log',
                                              'data-max-bytes': MAX_ATTACHMENT_BYTES}))

    def __init__(self, *args, demo_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        if demo_mode:
            self.fields['attachment'].help_text += ' Bản xem thử chỉ ghi nhận tên và dung lượng, chưa lưu nội dung file.'
        for field in self.fields.values():
            field.error_messages.update({
                'required': 'Vui lòng nhập hoặc chọn thông tin này.',
                'min_length': 'Vui lòng nhập ít nhất %(limit_value)s ký tự.',
                'max_length': 'Chỉ được nhập tối đa %(limit_value)s ký tự.',
                'invalid_choice': 'Lựa chọn không hợp lệ. Vui lòng chọn lại.',
            })

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            validate_attachment(attachment)
        return attachment


class ReplyForm(forms.Form):
    content = forms.CharField(
        label='Thêm phản hồi', min_length=3, max_length=2000,
        error_messages={'required': 'Vui lòng nhập nội dung phản hồi.',
                        'min_length': 'Phản hồi cần ít nhất 3 ký tự.',
                        'max_length': 'Phản hồi chỉ được dài tối đa 2.000 ký tự.'},
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                    'placeholder': 'Bổ sung thông tin hoặc trao đổi về sự cố…'}))
