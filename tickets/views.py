from django.shortcuts import render

def home(request):
    """Trang chu dung bo cuc chung cua giao dien nguoi dung."""
    return render(request, 'tickets/home.html')
