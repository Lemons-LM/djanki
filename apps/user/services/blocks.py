"""Block and unblock services."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.core.permissions import require
from apps.user.exceptions import InvalidBlock
from apps.user.models.block import Block


def block_user(
    *,
    target,
    blocked_by,
    reason: str = "",
    expires_at=None,
    autoblock: bool = False,
    no_create: bool = False,
) -> Block:
    """Create a block for ``target``.

    ``expires_at=None`` means an indefinite block. Past expiries and self-blocks are
    rejected. Requires the ``user.block_user`` permission.
    """
    require(blocked_by, "block")
    if target.pk == getattr(blocked_by, "pk", None):
        raise InvalidBlock("You cannot block yourself")
    if expires_at is not None and expires_at <= timezone.now():
        raise InvalidBlock("expires_at must be in the future")
    if getattr(target, "is_deleted", False):
        raise InvalidBlock("Cannot block a deleted user")

    with transaction.atomic():
        return Block.objects.create(
            target=target,
            blocked_by=blocked_by,
            blocked_by_name=getattr(blocked_by, "username", "") or "",
            reason=reason,
            expires_at=expires_at,
            autoblock=autoblock,
            no_create=no_create,
        )


def unblock_user(*, target, unblocked_by, reason: str = "") -> int:
    """Lift every currently active block for ``target``.

    Returns:
        The number of blocks that were lifted.

    Requires the ``user.unblock_user`` permission.
    """
    require(unblocked_by, "unblock")
    now = timezone.now()
    with transaction.atomic():
        return Block.active_for(target).update(
            unblocked_at=now,
            unblocked_by=unblocked_by,
            unblocked_by_name=getattr(unblocked_by, "username", "") or "",
            unblock_reason=reason,
        )


def active_blocks(target):
    """Return the blocks currently applying to ``target``."""
    return Block.active_for(target)
