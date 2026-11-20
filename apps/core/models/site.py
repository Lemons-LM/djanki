"""Site-wide configuration and site-level permissions."""

from django.db import models


class SiteConfig(models.Model):
    """Singleton site configuration row.

    This model hosts site-wide rights (read, interface editing, import/export) and the
    anonymous-read policy. The row is created by a data migration and by ``get_solo()``.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    site_name = models.CharField(max_length=255, default="Djanki")
    anonymous_read = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site configuration"
        verbose_name_plural = "Site configuration"
        permissions = [
            ("read", "Can read content"),
            ("edit_interface", "Can edit interface"),
            ("edit_content_model", "Can edit content models"),
            ("import_data", "Can import data"),
            ("export_data", "Can export data"),
        ]

    def __str__(self):
        return self.site_name

    @classmethod
    def get_solo(cls):
        """Return the singleton row, creating it if necessary."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        """Force the singleton primary key to ``1``."""
        self.pk = 1
        super().save(*args, **kwargs)
