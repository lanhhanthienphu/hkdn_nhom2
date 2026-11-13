from django.urls import path

from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.home, name='home'),
    path('tickets/', views.ticket_list, name='list'),
    path('tickets/new/', views.ticket_create, name='create'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='detail'),
    path('tickets/<int:ticket_id>/attachments/<int:attachment_id>/download/',
         views.attachment_download, name='attachment_download'),
    path('tickets/<int:ticket_id>/assign/', views.ticket_assign, name='assign'),
    path('tickets/<int:ticket_id>/status/', views.ticket_change_status, name='change_status'),
]
