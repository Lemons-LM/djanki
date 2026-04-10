from django.db import models

from apps.core.models.page import Page


class PageTitleIndex(models.Model):
    page = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        related_name='current_titles',
    )
    title = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        verbose_name = "Current Property Index"
        verbose_name_plural = "Current Property Indices"
        unique_together = ('page', 'title')

    def __str__(self):
        return f"Index: {self.title} -> {self.page.used_title}"
