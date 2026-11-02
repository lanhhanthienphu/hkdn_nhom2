from django.urls import path

from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.home, name='home'),
    path('tickets/', views.ticket_list, name='list'),
    path('tickets/new/', views.ticket_create, name='create'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='detail'),
]
