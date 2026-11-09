from django.urls import path

from . import api


app_name = "kb_api"

urlpatterns = [
    path("articles/", api.article_list, name="article_list"),
    path("articles/<int:pk>/", api.article_detail, name="article_detail"),
]
