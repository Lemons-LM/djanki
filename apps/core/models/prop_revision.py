from django.db import models

from apps.core.models.page import Page


class PropRevision(models.Model):
    page = models.ForeignKey(
        Page,
        on_delete=models.DO_NOTHING,
        related_name='prop_revisions',
        verbose_name="Pageid related"
    )
    titles = models.JSONField(verbose_name="Page title")

    content = models.JSONField(verbose_name="Property")
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
        verbose_name = "Prop Revision"
        verbose_name_plural = "Prop Revision list"
        ordering = ['-id']