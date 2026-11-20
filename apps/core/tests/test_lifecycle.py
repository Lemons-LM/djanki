"""Tests for delete, restore and protection behavior."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from apps.core.exceptions import PageNotFound, PermissionDenied
from apps.core.models import PageProtection, ProtectionLog
from apps.core.services.pages import (
    delete_page,
    edit_page,
    protect_page,
    restore_page,
)
from apps.core.services.titles import resolve_title
from apps.user.models import Block

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_delete_releases_titles_and_restore_rebinds(user, page):
    """Soft delete releases titles; restore rebuilds them."""
    delete_page(
        page_id=page.pk,
        author=user,
        base_revid=page.current_revision_id,
    )
    page.refresh_from_db()
    assert page.is_deleted is True
    assert page.title_bindings.filter(released_at__isnull=True).count() == 0
    with pytest.raises(PageNotFound):
        resolve_title("Main Page")

    restored = restore_page(
        page_id=page.pk,
        author=user,
        base_revid=page.current_revision_id,
    )
    assert restored.is_deleted is False
    assert resolve_title("Main Page").page.pk == page.pk


def test_protection_blocks_user_without_sysop(user, page):
    """A sysop-level edit protection rejects a normal editor."""
    editor = User.objects.create_user(username="editor", password="test-password")
    editor.groups.add(Group.objects.get(name="user"))

    protect_page(
        page_id=page.pk,
        author=user,
        protection={"edit": "sysop"},
        base_revid=page.current_revision_id,
    )

    with pytest.raises(PermissionDenied):
        edit_page(
            page_id=page.pk,
            author=editor,
            base_revid=page.current_revision_id,
            main="Blocked edit",
        )


def test_protection_writes_structured_rows_and_log(user, page):
    """Protection changes create structured rows and append history."""
    expires_at = timezone.now() + timedelta(days=1)
    protect_page(
        page_id=page.pk,
        author=user,
        protection={"edit": "sysop"},
        base_revid=page.current_revision_id,
        reason="temporary",
        expires_at=expires_at,
    )

    protection = PageProtection.objects.get(page=page, action="edit")
    assert protection.level == "sysop"
    assert protection.expires_at is not None
    log = ProtectionLog.objects.get(page=page, action="edit")
    assert log.old_level == "open"
    assert log.new_level == "sysop"

    PageProtection.objects.filter(pk=protection.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    page.refresh_from_db()
    assert page.protection_level("edit") == "open"


def test_blocked_user_cannot_edit(user, page):
    """A currently blocked user cannot create a revision."""
    editor = User.objects.create_user(username="blocked", password="test-password")
    editor.groups.add(Group.objects.get(name="user"))
    Block.objects.create(target=editor, blocked_by=user, reason="test")

    with pytest.raises(PermissionDenied):
        edit_page(
            page_id=page.pk,
            author=editor,
            base_revid=page.current_revision_id,
            main="Blocked edit",
        )
