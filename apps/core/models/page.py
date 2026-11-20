"""Page identity and current-state pointers."""

from django.db import models

from apps.core.constants import ProtectionLevel


class Page(models.Model):
    """A wiki page.

    The complete page state lives in the current revision's slots. ``current_revision``
    is nullable only during the creation transaction; the page service sets it before
    committing.
    """

    namespace = models.PositiveSmallIntegerField(default=0, db_index=True)
    current_revision = models.ForeignKey(
        "Revision",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="current_for_pages",
        verbose_name="Current revision",
    )
    revision_count = models.PositiveBigIntegerField(default=0)
    redirect_target = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="redirect_sources",
        verbose_name="Redirect target",
    )
    is_deleted = models.BooleanField(default=False)
    is_suppressed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        permissions = [
            ("edit_page", "Can edit pages"),
            ("move_page", "Can move pages"),
            ("protect_page", "Can protect pages"),
            ("suppress_page", "Can suppress pages"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(namespace__gte=0),
                name="page_namespace_nonnegative",
            ),
        ]
        indexes = [
            models.Index(fields=["namespace", "is_deleted"], name="idx_page_ns_deleted"),
            models.Index(fields=["is_deleted", "-updated_at"], name="idx_page_recent"),
        ]

    def __str__(self):
        return self.primary_title or f"Page {self.pk}"

    @property
    def primary_binding(self):
        """Return the active primary title binding, if any."""
        return self.title_bindings.filter(
            is_primary=True,
            released_at__isnull=True,
        ).first()

    @property
    def primary_title(self):
        """Return the active primary display title, or ``None``."""
        binding = self.primary_binding
        return binding.display_title if binding else None

    @property
    def canonical_title_key(self):
        """Return the normalized key of the active primary title, or ``None``."""
        binding = self.primary_binding
        return binding.normalized_title if binding else None

    @property
    def is_redirect(self) -> bool:
        """Return whether this page is a redirect."""
        return self.redirect_target_id is not None

    def protection_level(self, action: str) -> str:
        """Return the active protection level for ``action`` (default: open)."""
        protection = self.protections.filter(action=action).first()
        if protection is not None and protection.is_active:
            return protection.level
        return ProtectionLevel.OPEN

    @property
    def latest_slots(self) -> dict:
        """Return a ``role -> Content`` mapping for the current revision."""
        revision = self.current_revision
        if revision is None:
            return {}
        return {slot.role: slot.content for slot in revision.slots.select_related("content")}
