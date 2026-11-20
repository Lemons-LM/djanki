"""Tests for blocks and unblocks."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from apps.core.exceptions import PermissionDenied
from apps.user.exceptions import InvalidBlock
from apps.user.models import Block
from apps.user.services.blocks import block_user, unblock_user

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def target():
    """Return a normal user to block."""
    return User.objects.create_user(username="target", password="test-password")


def test_block_then_unblock(user, target):
    """Blocking is visible immediately; unblocking lifts all active blocks."""
    block = block_user(target=target, blocked_by=user, reason="vandalism")

    assert block.is_active is True
    assert target.is_currently_blocked is True

    assert unblock_user(target=target, unblocked_by=user, reason="appeal") == 1
    block.refresh_from_db()
    assert block.unblocked_at is not None
    assert target.is_currently_blocked is False


def test_expired_block_is_inactive(user, target):
    """A block whose expiry is in the past does not apply."""
    now = timezone.now()
    block = Block.objects.create(
        target=target,
        blocked_by=user,
        start_at=now - timedelta(days=2),
        expires_at=now - timedelta(days=1),
    )
    assert block.is_expired is True
    assert block.is_active is False
    assert target.is_currently_blocked is False


def test_block_rejects_past_expiry(user, target):
    """A block cannot be created already expired."""
    with pytest.raises(InvalidBlock):
        block_user(
            target=target,
            blocked_by=user,
            expires_at=timezone.now() - timedelta(seconds=1),
        )


def test_block_rejects_self(user):
    """Users cannot block themselves."""
    with pytest.raises(InvalidBlock):
        block_user(target=user, blocked_by=user)


def test_block_requires_permission(user, target):
    """A normal user without block rights cannot block."""
    editor = User.objects.create_user(username="editor", password="test-password")
    editor.groups.add(Group.objects.get(name="user"))

    with pytest.raises(PermissionDenied):
        block_user(target=target, blocked_by=editor, reason="nope")
