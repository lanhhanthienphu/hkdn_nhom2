from django.conf import settings
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Tên vai trò")
    description = models.CharField(max_length=255, blank=True, verbose_name="Mô tả")

    class Meta:
        db_table = "roles"
        verbose_name = "Vai trò"
        verbose_name_plural = "Các vai trò"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Tài khoản",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="user_profiles",
        null=True,
        blank=True,
        verbose_name="Vai trò",
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    department = models.CharField(max_length=100, blank=True, verbose_name="Phòng ban")

    class Meta:
        db_table = "user_profiles"
        verbose_name = "Hồ sơ người dùng"
        verbose_name_plural = "Hồ sơ người dùng"

    def __str__(self):
        role_name = self.role.name if self.role else "Chưa gán vai trò"
        return f"{self.user.username} ({role_name})"

    def is_admin(self) -> bool:
        if self.user.is_superuser:
            return True
        if self.role and self.role.name.lower() in ("admin", "quản trị viên", "quantri"):
            return True
        return False

    def is_technician(self) -> bool:
        if self.is_admin():
            return True
        if self.role and self.role.name.lower() in (
            "technician",
            "it support",
            "kỹ thuật viên",
            "kythuatvien",
            "support",
        ):
            return True
        return False

    def is_end_user(self) -> bool:
        return not self.is_technician()


from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_role = Role.objects.filter(name='user').first()
        UserProfile.objects.get_or_create(user=instance, defaults={'role': user_role})

