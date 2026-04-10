from django.db import migrations


def create_groups_with_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group_definitions = {
        'user': [
            'read',
            'edit',
            'move',
        ],
        'auto-confirmed': [
            'email',
            'upload'
        ],
        'sysop': [
            'read',
            'edit',
            'move',
            'delete',
            'protect',
            'import',
            'export',
            'block',
            'unblock',
        ],
        'interface-admin': [
            'edit-interface',
            'edit-content-model'
        ],
        'bot': [
            'bot'
        ],
        'suppress': [
            'suppress'
        ],
        'bureaucrat': [
            'user-rights'
        ]
    }

    for group_name, perms_codenames in group_definitions.items():
        group, created = Group.objects.get_or_create(name=group_name)

        permissions = Permission.objects.filter(
            codename__in=perms_codenames,
            content_type__app_label='user'
        )

        group.permissions.set(permissions)

        if created:
            print(f"Created group '{group_name}' with {len(permissions)} permissions.")
        else:
            print(f"Updated group '{group_name}' with {len(permissions)} permissions.")


class Migration(migrations.Migration):
    dependencies = [
        ('user', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups_with_permissions),
    ]