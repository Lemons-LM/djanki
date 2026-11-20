"""Structured page protection and its change log."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.constants import ProtectionAction, ProtectionLevel


class PageProtection(models.Model):
    """The current protection row for one page action.

    There is at most one row per ``(page, action)``. Expired rows are kept until the
    next protection update; ``is_active`` decides whether they apply.
    """

    page = models.ForeignKey(
        "Page",
        on_delete=models.PROTECT,
        related_name="protections",
        verbose_name="Page",
    )
    action = models.CharField(max_length=16, choices=ProtectionAction.choices)
    level = models.CharField(max_length=16, choices=ProtectionLevel.choices)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="set_protections",
    )
    set_by_name = models.CharField(max_length=150, blank=True, default="")
    set_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        verbose_name = "Page protection"
        verbose_name_plural = "Page protections"
        ordering = ["page_id", "action"]
        unique_together = ("page", "action")
        indexes = [
            models.Index(fields=["page", "action"], name="idx_protection_page_action"),
        ]

    def __str__(self):
        return f"{self.page_id}:{self.action}={self.level}"

    @property
    def is_active(self) -> bool:
        """Return whether this protection currently applies."""
        return self.expires_at is None or self.expires_at > timezone.now()


class ProtectionLog(models.Model):
    """An append-only protection change record."""

    page = models.ForeignKey(
        "Page",
        on_delete=models.PROTECT,
        related_name="protection_logs",
        verbose_name="Page",
    )
    action = models.CharField(max_length=16, choices=ProtectionAction.choices)
    old_level = models.CharField(max_length=16, choices=ProtectionLevel.choices)
    new_level = models.CharField(max_length=16, choices=ProtectionLevel.choices)
    expires_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=500, blank=True, default="")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="protection_changes",
    )
    changed_by_name = models.CharField(max_length=150, blank=True, default="")
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)
    revision = models.ForeignKey(
        "Revision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="protection_logs",
    )

    class Meta:
        verbose_name = "Protection log"
        verbose_name_plural = "Protection logs"
        ordering = ["-changed_at", "-id"]
        indexes = [
            models.Index(fields=["page", "action", "-changed_at"], name="idx_protection_log"),
        ]

    def __str__(self):
        return f"{self.page_id}:{self.action} {self.old_level}->{self.new_level}"
