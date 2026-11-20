"""Core model admin registrations."""

from django.contrib import admin

from apps.core.models import (
    Content,
    Page,
    PageProtection,
    ProtectionLog,
    Revision,
    RevisionSlot,
    SiteConfig,
    TitleBinding,
)


class RevisionSlotInline(admin.TabularInline):
    """Read-only inline showing a revision's slots."""

    model = RevisionSlot
    extra = 0
    can_delete = False
    readonly_fields = ("role", "content")

    def has_add_permission(self, request, obj=None):
        """Slots are created by services, not the admin."""
        return False


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """Read-only view of immutable content rows."""

    list_display = ("id", "content_model", "sha1", "size", "created_at")
    search_fields = ("sha1",)
    readonly_fields = (
        "content_model",
        "data",
        "sha1",
        "size",
        "created_at",
    )

    def has_add_permission(self, request):
        """Content is always created by services."""
        return False

    def has_change_permission(self, request, obj=None):
        """Content is immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Content is garbage-collected deliberately, not from admin."""
        return False


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    """Read-only revision history."""

    list_display = (
        "id",
        "page",
        "page_rev_number",
        "author",
        "created_at",
        "comment",
        "deleted",
        "suppressed",
    )
    list_filter = ("deleted", "suppressed", "minor", "bot")
    search_fields = ("comment", "author_name")
    inlines = [RevisionSlotInline]
    readonly_fields = (
        "page",
        "page_rev_number",
        "parent_revision",
        "author",
        "author_name",
        "author_ip",
        "comment",
        "created_at",
        "minor",
        "bot",
        "deleted",
        "suppressed",
    )

    def has_add_permission(self, request):
        """Revisions are always created by services."""
        return False

    def has_change_permission(self, request, obj=None):
        """Revisions are immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Revisions are never hard-deleted."""
        return False


class PageProtectionInline(admin.TabularInline):
    """Read-only inline of current protection rows."""

    model = PageProtection
    extra = 0
    can_delete = False
    readonly_fields = (
        "action",
        "level",
        "expires_at",
        "set_by",
        "set_by_name",
        "set_at",
        "reason",
    )

    def has_add_permission(self, request, obj=None):
        """Protection is changed through services."""
        return False


class ProtectionLogInline(admin.TabularInline):
    """Read-only inline of protection change history."""

    model = ProtectionLog
    extra = 0
    can_delete = False
    readonly_fields = (
        "action",
        "old_level",
        "new_level",
        "expires_at",
        "reason",
        "changed_by",
        "changed_by_name",
        "changed_at",
        "revision",
    )

    def has_add_permission(self, request, obj=None):
        """Protection logs are append-only."""
        return False


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Page state overview; writes go through services."""

    inlines = [PageProtectionInline, ProtectionLogInline]
    list_display = (
        "id",
        "display_title",
        "namespace",
        "current_revision",
        "is_redirect",
        "is_deleted",
        "is_suppressed",
        "updated_at",
    )
    list_filter = ("namespace", "is_deleted", "is_suppressed")
    search_fields = ("title_bindings__display_title",)
    readonly_fields = (
        "namespace",
        "current_revision",
        "revision_count",
        "redirect_target",
        "is_deleted",
        "is_suppressed",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Primary title")
    def display_title(self, obj):
        """Return the active primary title."""
        return obj.primary_title

    def has_add_permission(self, request):
        """Pages are created by services."""
        return False

    def has_change_permission(self, request, obj=None):
        """Page writes go through services."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Pages are soft-deleted, never hard-deleted."""
        return False


@admin.register(PageProtection)
class PageProtectionAdmin(admin.ModelAdmin):
    """Read-only current protection rows."""

    list_display = ("id", "page", "action", "level", "expires_at", "set_by_name", "set_at")
    list_filter = ("action", "level")
    readonly_fields = (
        "page",
        "action",
        "level",
        "expires_at",
        "set_by",
        "set_by_name",
        "set_at",
        "reason",
    )

    def has_add_permission(self, request):
        """Protection is changed through services."""
        return False

    def has_change_permission(self, request, obj=None):
        """Protection is changed through services."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Protection rows are removed by services."""
        return False


@admin.register(ProtectionLog)
class ProtectionLogAdmin(admin.ModelAdmin):
    """Read-only protection change history."""

    list_display = (
        "id",
        "page",
        "action",
        "old_level",
        "new_level",
        "changed_by_name",
        "changed_at",
    )
    list_filter = ("action", "old_level", "new_level")
    readonly_fields = (
        "page",
        "action",
        "old_level",
        "new_level",
        "expires_at",
        "reason",
        "changed_by",
        "changed_by_name",
        "changed_at",
        "revision",
    )

    def has_add_permission(self, request):
        """Protection logs are append-only."""
        return False

    def has_change_permission(self, request, obj=None):
        """Protection logs are immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Protection logs are never hard-deleted."""
        return False


@admin.register(TitleBinding)
class TitleBindingAdmin(admin.ModelAdmin):
    """Read-only title binding history."""

    list_display = (
        "id",
        "page",
        "display_title",
        "namespace",
        "is_primary",
        "is_active",
        "created_at",
        "released_at",
    )
    list_filter = ("namespace", "is_primary")
    search_fields = ("display_title", "normalized_title")
    readonly_fields = (
        "page",
        "namespace",
        "display_title",
        "normalized_title",
        "is_primary",
        "created_revision",
        "released_revision",
        "created_at",
        "released_at",
    )

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        """Return whether the binding is active."""
        return obj.is_active

    def has_add_permission(self, request):
        """Bindings are projections maintained by services."""
        return False

    def has_change_permission(self, request, obj=None):
        """Bindings are projections maintained by services."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Binding history is never deleted."""
        return False


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    """Singleton site configuration."""

    list_display = ("id", "site_name", "anonymous_read", "updated_at")

    def has_add_permission(self, request):
        """The singleton is seeded by migration."""
        return False

    def has_delete_permission(self, request, obj=None):
        """The singleton must remain."""
        return False
