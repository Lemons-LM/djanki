"""Group definitions and idempotent permission seeding."""

from __future__ import annotations

from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate
from django.dispatch import receiver

GROUP_PERMISSIONS = {
    "user": [
        "core.read",
        "core.edit_page",
        "core.move_page",
    ],
    "autoconfirmed": [
        "core.read",
        "core.edit_page",
        "core.move_page",
        "user.send_email",
        "file.upload_file",
    ],
    "sysop": [
        "core.read",
        "core.edit_page",
        "core.move_page",
        "core.delete_page",
        "core.protect_page",
        "core.import_data",
        "core.export_data",
        "user.block_user",
        "user.unblock_user",
    ],
    "interface-admin": [
        "core.read",
        "core.edit_interface",
        "core.edit_content_model",
    ],
    "bot": [
        "core.read",
        "core.edit_page",
        "user.bot",
    ],
    "suppress": [
        "core.read",
        "core.suppress_page",
    ],
    "bureaucrat": [
        "core.read",
        "user.change_user_rights",
    ],
}


def seed_groups(*, using: str = DEFAULT_DB_ALIAS, apps=None, verbosity: int = 0) -> dict:
    """Create or update the standard groups and their permission sets.

    The function is idempotent: rerunning it replaces each group's permissions with the
    configured list, removing stale assignments.

    Raises:
        ImproperlyConfigured: If a configured permission codename does not exist.
    """
    # Make seeding deterministic even if this runs before the built-in receiver.
    # Use the real app registry: the migration registry contains AppConfigStub
    # objects for apps without models, which create_permissions cannot handle.
    for app_config in global_apps.get_app_configs():
        create_permissions(app_config, using=using, apps=global_apps, verbosity=0)

    result = {}
    for group_name, permission_labels in GROUP_PERMISSIONS.items():
        group, _ = Group.objects.using(using).get_or_create(name=group_name)
        permissions = []
        for label in permission_labels:
            app_label, codename = label.split(".", 1)
            try:
                permission = Permission.objects.using(using).get(
                    content_type__app_label=app_label,
                    codename=codename,
                )
            except Permission.DoesNotExist as exc:
                raise ImproperlyConfigured(
                    f"Permission '{label}' for group '{group_name}' does not exist"
                ) from exc
            permissions.append(permission)
        group.permissions.set(permissions)
        result[group_name] = len(permissions)

    return result


@receiver(post_migrate, dispatch_uid="user.seed_groups_post_migrate")
def seed_groups_after_migrate(sender, using=DEFAULT_DB_ALIAS, apps=None, verbosity=0, **kwargs):
    """Seed groups after migrations, once the permission rows exist."""
    if getattr(sender, "label", None) != "user":
        return
    seed_groups(using=using, apps=apps, verbosity=verbosity)
