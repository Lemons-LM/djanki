"""Minimal file metadata model.

Actual upload/storage behavior is out of scope for the core revision refactor. This
model exists so file permissions have a correct owner.
"""

from django.conf import settings
from django.db import models


class File(models.Model):
    """Metadata for an uploaded file."""

    title = models.CharField(max_length=255)
    namespace = models.PositiveSmallIntegerField(default=6)
    storage_key = models.CharField(max_length=512, unique=True)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=127, blank=True, default="")
    size = models.PositiveBigIntegerField(default=0)
    sha1 = models.CharField(max_length=40, db_index=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_files",
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"
        permissions = [
            ("upload_file", "Can upload files"),
            ("move_file", "Can move files"),
        ]

    def __str__(self):
        return self.title
