from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_published",
        "created_at",
        "updated_at",
    )
    search_fields = ("title", "content")
    list_filter = ("is_published", "created_at")
    readonly_fields = ("created_at", "updated_at")