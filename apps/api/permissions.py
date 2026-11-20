"""DRF permission classes backed by the core ``can()`` service."""

from rest_framework.permissions import BasePermission

from apps.core.permissions import can


class CanReadPage(BasePermission):
    """Allow reads according to global and page-level rules."""

    def has_permission(self, request, view):
        """Defer page-specific checks to object permission."""
        return True

    def has_object_permission(self, request, view, obj):
        """Check read access to a page."""
        return can(request.user, "read", obj)


class CanEditPage(BasePermission):
    """Allow edits according to global and page-level rules."""

    def has_object_permission(self, request, view, obj):
        """Check edit access to a page."""
        return can(request.user, "edit", obj)


class CanMovePage(BasePermission):
    """Allow moves according to global and page-level rules."""

    def has_object_permission(self, request, view, obj):
        """Check move access to a page."""
        return can(request.user, "move", obj)


class CanDeletePage(BasePermission):
    """Allow deletion according to global and page-level rules."""

    def has_object_permission(self, request, view, obj):
        """Check delete access to a page."""
        return can(request.user, "delete", obj)


class CanProtectPage(BasePermission):
    """Allow protection changes according to global and page-level rules."""

    def has_object_permission(self, request, view, obj):
        """Check protect access to a page."""
        return can(request.user, "protect", obj)
