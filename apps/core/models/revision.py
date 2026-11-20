"""Revision header and global revision identity."""

import re

from django.conf import settings
from django.db import models
from django.utils import timezone


class Revision(models.Model):
    """One page-state-changing edit.

    ``id`` is the global MediaWiki-compatible ``revid``. ``page_rev_number`` is a
    per-page sequence used for the readable ``p{page_id}-r{number}`` slug.
    """

    SLUG_RE = re.compile(r"^p(?P<page_id>\d+)-r(?P<number>\d+)$")

    page = models.ForeignKey(
        "Page",
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Page",
    )
    page_rev_number = models.PositiveBigIntegerField()
    parent_revision = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        verbose_name="Parent revision",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="revisions",
        verbose_name="Author",
    )
    author_name = models.CharField(max_length=150, blank=True, default="")
    author_ip = models.GenericIPAddressField(null=True, blank=True)
    comment = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    minor = models.BooleanField(default=False)
    bot = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    suppressed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Revision"
        verbose_name_plural = "Revisions"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["page", "page_rev_number"],
                name="uniq_revision_page_number",
            ),
        ]
        indexes = [
            models.Index(
                fields=["page", "-page_rev_number"],
                name="idx_revision_page_history",
            ),
        ]

    def __str__(self):
        return f"{self.slug} (revid {self.pk})"

    @property
    def slug(self) -> str:
        """Return the readable ``p{page_id}-r{number}`` revision slug."""
        return f"p{self.page_id}-r{self.page_rev_number}"

    @classmethod
    def parse_slug(cls, value: str):
        """Parse a revision slug.

        Returns:
            A ``(page_id, page_rev_number)`` tuple, or ``None`` if the value is not
            a valid slug.
        """
        match = cls.SLUG_RE.match((value or "").strip())
        if not match:
            return None
        return int(match.group("page_id")), int(match.group("number"))
