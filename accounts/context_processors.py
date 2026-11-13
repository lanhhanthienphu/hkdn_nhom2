def user_roles(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'is_admin': False,
            'is_technician': False,
            'role_name': '',
            'role_badge_class': '',
        }

    is_admin = False
    is_tech = False
    role_name = 'Người dùng'
    role_badge_class = 'bg-secondary'

    if user.is_superuser:
        is_admin = True
        is_tech = True
        role_name = 'Quản trị viên'
        role_badge_class = 'bg-danger'
    elif hasattr(user, 'profile'):
        if user.profile.is_admin():
            is_admin = True
            is_tech = True
            role_name = 'Quản trị viên'
            role_badge_class = 'bg-danger'
        elif user.profile.is_technician():
            is_tech = True
            role_name = 'Kỹ thuật viên'
            role_badge_class = 'bg-primary'
        else:
            role_name = 'Người dùng'
            role_badge_class = 'bg-secondary'

    return {
        'is_admin': is_admin,
        'is_technician': is_tech,
        'role_name': role_name,
        'role_badge_class': role_badge_class,
    }

