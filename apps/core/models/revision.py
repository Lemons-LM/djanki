from django.db import models

from apps.core.models.page import Page


class PageRevision(models.Model):
    page = models.ForeignKey(
        Page,
        on_delete=models.DO_NOTHING,
        related_name='revisions',
        verbose_name="Pageid related"
    )

    content = models.TextField(verbose_name="Text")
    author = models.ForeignKey(
        'User',
        on_delete=models.DO_NOTHING,
        related_name='revision',
        verbose_name="Author"
    )
    deleted = models.BooleanField(default=False, verbose_name="Deleted")
    suppressed = models.BooleanField(default=False, verbose_name="Suppressed")

    created_at = models.DateTimeField(auto_now_add=False)
    comment = models.CharField(max_length=255, blank=True, default="", verbose_name="Edit comment")

    class Meta:
        verbose_name = "Revision"
        verbose_name_plural = "Revision list"

