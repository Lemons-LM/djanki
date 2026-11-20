"""Category bindings: a rebuildable projection of the categories property."""

from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.namespaces import CATEGORY


class CategoryBinding(models.Model):
    """The lifetime of a page's membership in one category.

    Rows are never physically deleted. The active predicate is
    ``released_at IS NULL``; releasing a membership preserves history.
    """

    page = models.ForeignKey(
        "core.Page",
        on_delete=models.PROTECT,
        related_name="category_bindings",
        verbose_name="Page",
    )
    namespace = models.PositiveSmallIntegerField(default=CATEGORY, db_index=True)
    display_title = models.CharField(max_length=255)
    normalized_title = models.CharField(max_length=255, db_index=True)
    created_revision = models.ForeignKey(
        "core.Revision",
        on_delete=models.PROTECT,
        related_name="created_category_bindings",
    )
    released_revision = models.ForeignKey(
        "core.Revision",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="released_category_bindings",
    )
    created_at = models.DateTimeField(default=timezone.now)
    released_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "Category binding"
        verbose_name_plural = "Category bindings"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["page", "namespace", "normalized_title"],
                condition=models.Q(released_at__isnull=True),
                name="uniq_active_category_binding",
            ),
        ]
        indexes = [
            models.Index(
                fields=["namespace", "normalized_title", "released_at"],
                name="idx_category_active_lookup",
            ),
            models.Index(
                fields=["page", "released_at"],
                name="idx_category_page_active",
            ),
        ]

    def __str__(self):
        state = "active" if self.is_active else "released"
        return f"{self.full_title} -> page {self.page_id} ({state})"

    @property
    def is_active(self) -> bool:
        """Return whether this category membership currently applies."""
        return self.released_at is None

    @property
    def full_title(self) -> str:
        """Return the category title including its namespace prefix."""
        return f"Category:{self.display_title}"
