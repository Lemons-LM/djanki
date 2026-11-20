"""Tests for page creation, editing and revision invariants."""

import pytest

from apps.core.exceptions import EditConflict, TitleConflict
from apps.core.models.page import Page
from apps.core.models.title_binding import TitleBinding
from apps.core.services.pages import create_page, edit_page
from apps.core.services.revisions import get_revision_state
from apps.core.services.titles import rebuild_title_bindings, resolve_title

pytestmark = pytest.mark.django_db


def test_create_page_creates_two_slots_and_primary_binding(user):
    """A new page has a full slot map and exactly one active primary title."""
    page = create_page(
        title="Main Page",
        main_content="Hello",
        author=user,
        properties={
            "schema": 1,
            "titles": {"primary": "Main Page", "aliases": ["Home"]},
        },
    )

    assert page.current_revision is not None
    state = get_revision_state(page.current_revision)
    assert set(state) == {"main", "properties"}
    assert page.revision_count == 1

    active = page.title_bindings.filter(released_at__isnull=True)
    assert active.count() == 2
    assert active.filter(is_primary=True).count() == 1
    assert page.primary_title == "Main Page"


def test_edit_reuses_unchanged_slots(user, page):
    """Editing main content reuses the current properties Content row."""
    state_before = get_revision_state(page.current_revision)
    revision = edit_page(
        page_id=page.pk,
        author=user,
        base_revid=page.current_revision_id,
        main="Hello again",
    )
    state_after = get_revision_state(revision)

    assert state_after["properties"].pk == state_before["properties"].pk
    assert state_after["main"].pk != state_before["main"].pk


def test_edit_reuses_main_when_only_properties_change(user, page):
    """Editing properties reuses the current main Content row."""
    state_before = get_revision_state(page.current_revision)
    revision = edit_page(
        page_id=page.pk,
        author=user,
        base_revid=page.current_revision_id,
        properties={
            "schema": 1,
            "titles": {"primary": "Main Page", "aliases": ["Home"]},
        },
    )
    state_after = get_revision_state(revision)

    assert state_after["main"].pk == state_before["main"].pk
    assert state_after["properties"].pk != state_before["properties"].pk


def test_stale_base_revid_rolls_back(user, page):
    """A stale edit raises and leaves the page unchanged."""
    old_revid = page.current_revision_id
    new_revision = edit_page(
        page_id=page.pk,
        author=user,
        base_revid=old_revid,
        main="First edit",
    )

    with pytest.raises(EditConflict):
        edit_page(
            page_id=page.pk,
            author=user,
            base_revid=old_revid,
            main="Stale edit",
        )

    page.refresh_from_db()
    assert page.current_revision_id == new_revision.pk
    assert page.revision_count == 2


def test_alias_resolves_to_primary(user):
    """An alias resolves to the page's canonical primary title."""
    page = create_page(
        title="Main Page",
        main_content="Hello",
        author=user,
        properties={
            "schema": 1,
            "titles": {"primary": "Main Page", "aliases": ["Home"]},
        },
    )

    resolution = resolve_title("Home")
    assert resolution.page.pk == page.pk
    assert resolution.is_alias is True
    assert resolution.canonical_binding.display_title == "Main Page"


def test_removed_alias_keeps_history(user):
    """Removing an alias releases its binding but keeps the page association."""
    page = create_page(
        title="Main Page",
        main_content="Hello",
        author=user,
        properties={
            "schema": 1,
            "titles": {"primary": "Main Page", "aliases": ["Home"]},
        },
    )
    revid = page.current_revision_id
    assert revid is not None
    edit_page(
        page_id=page.pk,
        author=user,
        base_revid=revid,
        properties={"schema": 1, "titles": {"primary": "Main Page", "aliases": []}},
    )

    released = TitleBinding.objects.get(
        normalized_title="home",
        released_at__isnull=False,
    )
    assert released.page_id == page.pk


def test_title_rebuild_is_idempotent(user, page):
    """A healthy projection reports no changes in check mode."""
    report = rebuild_title_bindings(check_only=True)
    assert report.released == 0
    assert report.created == 0
    assert report.conflicts == 0


def test_title_conflict_is_rejected(user):
    """A title active on one page cannot be claimed by another."""
    create_page(title="Other Page", main_content="Other", author=user)

    with pytest.raises(TitleConflict):
        create_page(
            title="Second Page",
            main_content="Second",
            author=user,
            properties={
                "schema": 1,
                "titles": {"primary": "Second Page", "aliases": ["Other Page"]},
            },
        )

    assert Page.objects.count() == 1
