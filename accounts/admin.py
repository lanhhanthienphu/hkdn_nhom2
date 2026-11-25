from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import Role, UserProfile

User = get_user_model()


class AccountAdminPermissionMixin:
    """Require the Helpdesk admin role in addition to Django admin permissions."""

    def _has_admin_role(self, request):
        user = request.user
        if not user.is_authenticated or not user.is_active or not user.is_staff:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, 'profile', None)
        return profile is not None and profile.is_admin()

    def has_module_permission(self, request):
        return self._has_admin_role(request) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return self._has_admin_role(request) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return self._has_admin_role(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_admin_role(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._has_admin_role(request) and super().has_delete_permission(request, obj)


@admin.register(Role)
class RoleAdmin(AccountAdminPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name', 'description')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Hồ sơ người dùng'
    fk_name = 'user'


@admin.register(UserProfile)
class UserProfileAdmin(AccountAdminPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'user', 'role', 'phone', 'department')
    list_filter = ('role', 'department')
    search_fields = ('user__username', 'user__email', 'phone', 'department')


# Apply the same policy to every account/role administration entry point.
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(AccountAdminPermissionMixin, BaseUserAdmin):
    inlines = (UserProfileInline,)


@admin.register(Group)
class GroupAdmin(AccountAdminPermissionMixin, BaseGroupAdmin):
    pass
