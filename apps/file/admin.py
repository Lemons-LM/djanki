"""File metadata admin registration."""

from django.contrib import admin

from apps.file.models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """Minimal read-mostly file metadata admin."""

    list_display = (
        "id",
        "title",
        "original_name",
        "mime_type",
        "size",
        "uploaded_by",
        "is_deleted",
        "created_at",
    )
    list_filter = ("namespace", "is_deleted")
    search_fields = ("title", "original_name", "sha1")
