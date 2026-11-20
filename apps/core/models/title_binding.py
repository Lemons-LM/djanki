"""Title bindings: a rebuildable projection of the titles property."""

from django.db import models
from django.utils import timezone


class TitleBinding(models.Model):
    """The lifetime of a title belonging to a page.

    Rows are never physically deleted. The active predicate is ``released_at IS NULL``.
    Releasing a title preserves the former page association for history queries.
    """

    page = models.ForeignKey(
        "Page",
        on_delete=models.PROTECT,
        related_name="title_bindings",
        verbose_name="Page",
    )
    namespace = models.PositiveSmallIntegerField(default=0, db_index=True)
    display_title = models.CharField(max_length=255)
    normalized_title = models.CharField(max_length=255, db_index=True)
    is_primary = models.BooleanField(default=False)
    created_revision = models.ForeignKey(
        "Revision",
        on_delete=models.PROTECT,
        related_name="created_title_bindings",
    )
    released_revision = models.ForeignKey(
        "Revision",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="released_title_bindings",
    )
    created_at = models.DateTimeField(default=timezone.now)
    released_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "Title binding"
        verbose_name_plural = "Title bindings"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["namespace", "normalized_title"],
                condition=models.Q(released_at__isnull=True),
                name="uniq_active_title_binding",
            ),
            models.UniqueConstraint(
                fields=["page"],
                condition=models.Q(is_primary=True, released_at__isnull=True),
                name="uniq_active_primary_per_page",
            ),
            models.CheckConstraint(
                condition=~models.Q(display_title=""),
                name="title_binding_display_nonempty",
            ),
            models.CheckConstraint(
                condition=~models.Q(normalized_title=""),
                name="title_binding_normalized_nonempty",
            ),
        ]
        indexes = [
            models.Index(
                fields=["namespace", "normalized_title", "released_at"],
                name="idx_title_active_lookup",
            ),
            models.Index(
                fields=["page", "released_at"],
                name="idx_title_page_active",
            ),
            models.Index(
                fields=["normalized_title", "released_at"],
                name="idx_title_history",
            ),
        ]

    def __str__(self):
        state = "active" if self.is_active else "released"
        return f"{self.display_title} -> page {self.page_id} ({state})"

    @property
    def is_active(self) -> bool:
        """Return whether this binding currently owns the title."""
        return self.released_at is None
