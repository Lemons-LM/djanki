"""User blocks with history and expiry."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q, QuerySet
from django.utils import timezone


class Block(models.Model):
    """A block against a user.

    Blocks are append-only history. An active block is one that has not been lifted,
    has started, has not expired and has not been deleted. Re-blocking a user creates
    another row; unblocking lifts every currently active row.
    """

    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="blocks",
        verbose_name="Blocked user",
    )
    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="issued_blocks",
        verbose_name="Blocked by",
    )
    blocked_by_name = models.CharField(max_length=150, blank=True, default="")
    reason = models.CharField(max_length=500, blank=True, default="")

    start_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    unblocked_at = models.DateTimeField(null=True, blank=True)
    unblocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lifted_blocks",
        verbose_name="Unblocked by",
    )
    unblocked_by_name = models.CharField(max_length=150, blank=True, default="")
    unblock_reason = models.CharField(max_length=500, blank=True, default="")

    autoblock = models.BooleanField(default=False)
    no_create = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Block"
        verbose_name_plural = "Blocks"
        ordering = ["-start_at", "-id"]
        indexes = [
            models.Index(
                fields=["target", "unblocked_at", "expires_at"],
                name="idx_block_target_active",
            ),
        ]

    def __str__(self):
        state = "active" if self.is_active else "inactive"
        return f"Block {self.pk} on {self.target_id} ({state})"

    @property
    def is_expired(self) -> bool:
        """Return whether the block has an expiry in the past."""
        return self.expires_at is not None and self.expires_at <= timezone.now()

    @property
    def is_active(self) -> bool:
        """Return whether this block currently applies."""
        now = timezone.now()
        return (
            not self.is_deleted
            and self.unblocked_at is None
            and self.start_at <= now
            and (self.expires_at is None or self.expires_at > now)
        )

    @classmethod
    def active_for(cls, user) -> QuerySet["Block"]:
        """Return the queryset of blocks currently applying to ``user``."""
        if not getattr(user, "pk", None):
            return cls.objects.none()
        now = timezone.now()
        return cls.objects.filter(
            target=user,
            unblocked_at__isnull=True,
            is_deleted=False,
            start_at__lte=now,
        ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
