"""Property app admin registrations."""

from django.contrib import admin

from apps.property.models import CategoryBinding


@admin.register(CategoryBinding)
class CategoryBindingAdmin(admin.ModelAdmin):
    """Read-only category binding history."""

    list_display = (
        "id",
        "page",
        "full_title",
        "is_active",
        "created_at",
        "released_at",
    )
    list_filter = ("namespace",)
    search_fields = ("display_title", "normalized_title")
    readonly_fields = (
        "page",
        "namespace",
        "display_title",
        "normalized_title",
        "created_revision",
        "released_revision",
        "created_at",
        "released_at",
    )

    @admin.display(description="Category")
    def full_title(self, obj):
        """Return the namespace-prefixed category title."""
        return obj.full_title

    @admin.display(boolean=True, description="Active")
    def is_active(self, obj):
        """Return whether the binding is active."""
        return obj.is_active

    def has_add_permission(self, request):
        """Bindings are maintained by services."""
        return False

    def has_change_permission(self, request, obj=None):
        """Bindings are maintained by services."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Binding history is never deleted."""
        return False
