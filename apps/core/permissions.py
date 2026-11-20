"""Global and object-level permission checks."""

from __future__ import annotations

from apps.core.constants import ProtectionLevel
from apps.core.exceptions import PermissionDenied

PERMISSION_MAP = {
    "read": "core.read",
    "edit": "core.edit_page",
    "move": "core.move_page",
    "delete": "core.delete_page",
    "restore": "core.delete_page",
    "protect": "core.protect_page",
    "suppress": "core.suppress_page",
    "import": "core.import_data",
    "export": "core.export_data",
    "upload": "file.upload_file",
    "move_file": "file.move_file",
    "block": "user.block_user",
    "unblock": "user.unblock_user",
    "change_user_rights": "user.change_user_rights",
    "send_email": "user.send_email",
}

MW_RIGHTS = {
    "read": "core.read",
    "edit": "core.edit_page",
    "move": "core.move_page",
    "delete": "core.delete_page",
    "protect": "core.protect_page",
    "suppressrevision": "core.suppress_page",
    "import": "core.import_data",
    "export": "core.export_data",
    "upload": "file.upload_file",
    "movefile": "file.move_file",
    "block": "user.block_user",
    "unblock": "user.unblock_user",
    "userrights": "user.change_user_rights",
    "sendemail": "user.send_email",
    "bot": "user.bot",
    "editinterface": "core.edit_interface",
    "editcontentmodel": "core.edit_content_model",
}


def _is_authenticated(user) -> bool:
    return bool(getattr(user, "is_authenticated", False))


def _has_perm(user, permission: str) -> bool:
    return _is_authenticated(user) and user.has_perm(permission)


def _in_group(user, name: str) -> bool:
    return _is_authenticated(user) and user.groups.filter(name=name).exists()


def _can_read(user, page) -> bool:
    from apps.core.models.site import SiteConfig

    if not _is_authenticated(user):
        if not SiteConfig.get_solo().anonymous_read:
            return False
    else:
        if getattr(user, "is_deleted", False) or not getattr(user, "is_active", True):
            return False
        if not (getattr(user, "is_superuser", False) or _has_perm(user, "core.read")):
            return False

    if page is None:
        return True

    if page.is_deleted or page.is_suppressed:
        if not _is_authenticated(user):
            return False
        if not (
            getattr(user, "is_superuser", False)
            or _has_perm(user, "core.suppress_page")
            or _has_perm(user, "core.delete_page")
        ):
            return False

    if page.current_revision_id and page.current_revision.suppressed:
        if not _is_authenticated(user):
            return False
        if not (getattr(user, "is_superuser", False) or _has_perm(user, "core.suppress_page")):
            return False

    return True


def can(user, action: str, page=None) -> bool:
    """Return whether ``user`` may perform ``action``, optionally on ``page``."""
    if action not in PERMISSION_MAP:
        raise ValueError(f"Unknown action: {action}")

    if action == "read":
        return _can_read(user, page)

    if not _is_authenticated(user):
        return False
    if getattr(user, "is_deleted", False) or not getattr(user, "is_active", True):
        return False
    if getattr(user, "is_currently_blocked", False):
        return False

    if not (getattr(user, "is_superuser", False) or _has_perm(user, PERMISSION_MAP[action])):
        return False

    if page is None:
        return True

    if page.is_deleted and action not in ("delete", "restore"):
        return False

    level = page.protection_level(action)
    if level == ProtectionLevel.SYSOP and not (
        getattr(user, "is_superuser", False) or _in_group(user, "sysop")
    ):
        return False
    if level == ProtectionLevel.AUTOCONFIRMED and not (
        getattr(user, "is_superuser", False) or _in_group(user, "autoconfirmed")
    ):
        return False
    return True


def require(user, action: str, page=None) -> None:
    """Raise ``PermissionDenied`` unless ``user`` may perform ``action``."""
    if not can(user, action, page):
        raise PermissionDenied(
            details={
                "action": action,
                "page_id": getattr(page, "pk", None),
            }
        )
