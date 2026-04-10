from django.db import models
from django.utils import timezone

from apps.core.models.prop_revision import PropRevision
from apps.core.models.revision import PageRevision


class Page(models.Model):
    used_title = models.CharField(max_length=255, verbose_name="页面标题")

    titles = models.ForeignKey(
        'PageTitleIndex',
        on_delete=models.DO_NOTHING,
        related_name='+',
        verbose_name="Page title"
    )
    protection = models.CharField(default="", verbose_name="Protected")
    current_revision = models.ForeignKey(
        'PageRevision',
        on_delete=models.DO_NOTHING,
        null=False,
        blank=False,
        related_name='+',
        verbose_name="Current revision"
    )

    current_property_revision = models.ForeignKey(
        'PropRevision',
        on_delete=models.DO_NOTHING,
        null=False,
        blank=False,
        related_name='+',
        verbose_name="Current property revision"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "All Pages"

    def __str__(self):
        return self.title

    def get_all_revs(self):
        return self.revisions.all().order_by('-key')

    def get_all_property_revs(self):
        return self.prop_revisions.all().order_by('-key')

    def new_rev(self, *, content_data: str, author: 'User', edit_comment: str = '', **kwargs):
        rev = PageRevision.objects.create(
            page=self,
            content=content_data,
            author=author,
            created_at=timezone.now(),
            comment=edit_comment,
            ** kwargs
        )

        self.current_revision = rev
        self.save(update_fields=['current_revision', 'updated_at'])

        return rev

    def new_prop_rev(self, prop_data,author: 'User', edit_comment: str = '', **kwargs):
        prop_rev = PropRevision.objects.create(
            page=self,
            content=prop_data,
            author=author,
            created_at=timezone.now(),
            comment=edit_comment,
            ** kwargs
        )

        self.current_property_revision = prop_rev
        self.save(update_fields=['current_property_revision', 'updated_at'])

        return prop_rev