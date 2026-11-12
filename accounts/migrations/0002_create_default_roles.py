from django.db import migrations


def create_default_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    default_roles = [
        ('admin', 'Quản trị viên hệ thống'),
        ('technician', 'Kỹ thuật viên IT Support'),
        ('user', 'Người dùng cuối / Nhân viên'),
    ]
    for name, desc in default_roles:
        Role.objects.get_or_create(name=name, defaults={'description': desc})


def remove_default_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.filter(name__in=['admin', 'technician', 'user']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_roles, remove_default_roles),
    ]

