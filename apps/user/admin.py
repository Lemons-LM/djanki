"""User admin registration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.user.models import Block, WikiUser


@admin.register(WikiUser)
class WikiUserAdmin(UserAdmin):
    """Expose wiki-specific user fields in the standard user admin."""

    fieldsets = tuple(UserAdmin.fieldsets or ()) + (
        (
            "Wiki profile",
            {
                "fields": (
                    "phone",
                    "real_name",
                    "is_deleted",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "real_name",
        "is_staff",
        "is_blocked_now",
        "is_deleted",
    )

    @admin.display(boolean=True, description="Blocked now")
    def is_blocked_now(self, obj):
        """Return whether the user has an active block."""
        return obj.is_currently_blocked


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """Read-only block history; block/unblock through services."""

    list_display = (
        "id",
        "target",
        "blocked_by_name",
        "reason",
        "start_at",
        "expires_at",
        "unblocked_at",
        "autoblock",
        "no_create",
    )
    list_filter = ("autoblock", "no_create", "is_deleted")
    search_fields = ("target__username", "blocked_by_name", "reason", "unblock_reason")
    readonly_fields = (
        "target",
        "blocked_by",
        "blocked_by_name",
        "reason",
        "start_at",
        "expires_at",
        "unblocked_at",
        "unblocked_by",
        "unblocked_by_name",
        "unblock_reason",
        "autoblock",
        "no_create",
        "is_deleted",
        "created_at",
    )

    def has_add_permission(self, request):
        """Blocks are created by services."""
        return False

    def has_change_permission(self, request, obj=None):
        """Block history is immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Block history is never hard-deleted."""
        return False
