from django.db import models


class Article(models.Model):
    title = models.CharField("Tiêu đề", max_length=200)
    content = models.TextField("Nội dung hướng dẫn")
    is_published = models.BooleanField("Đã xuất bản", default=False)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)
    updated_at = models.DateTimeField("Ngày cập nhật", auto_now=True)

    class Meta:
        verbose_name = "Bài hướng dẫn"
        verbose_name_plural = "Bài hướng dẫn"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title