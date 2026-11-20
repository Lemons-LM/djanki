"""Tests for category binding projection."""

import pytest

from apps.core.services.pages import create_page, delete_page, edit_page
from apps.property.models import CategoryBinding
from apps.property.services.categories import rebuild_category_bindings

pytestmark = pytest.mark.django_db


def properties(categories):
    """Return a complete properties object with the given categories."""
    return {
        "schema": 1,
        "titles": {"primary": "Main Page", "aliases": []},
        "categories": categories,
    }


def test_create_page_syncs_categories(user):
    """Categories in the properties slot create active bindings."""
    page = create_page(
        title="Main Page",
        main_content="Hello",
        author=user,
        properties=properties(["Category:People", "Category:Stubs"]),
    )

    active = page.category_bindings.filter(released_at__isnull=True)
    assert active.count() == 2
    assert set(active.values_list("display_title", flat=True)) == {"People", "Stubs"}


def test_removed_category_keeps_history(user):
    """Removing a category releases its binding without deleting history."""
    page = create_page(
        title="Main Page",
        main_content="Hello",
        author=user,
        properties=properties(["Category:People", "Category:Stubs"]),
    )
    revid = page.current_revision_id
    assert revid is not None
    edit_page(
        page_id=page.pk,
        author=user,
        base_revid=revid,
        properties=properties(["Category:People"]),
    )

    released = CategoryBinding.objects.get(
        page=page,
        normalized_title="stubs",
        released_at__isnull=False,
    )
    assert released.page_id == page.pk
    assert page.category_bindings.filter(released_at__isnull=True).count() == 1


def test_multiple_pages_can_share_a_category(user):
    """Category membership is not globally unique across pages."""
    first = create_page(
        title="First",
        main_content="One",
        author=user,
        properties={
            "schema": 1,
            "titles": {"primary": "First", "aliases": []},
            "categories": ["Category:People"],
        },
    )
    second = create_page(
        title="Second",
        main_content="Two",
        author=user,
        properties={
            "schema": 1,
            "titles": {"primary": "Second", "aliases": []},
            "categories": ["Category:People"],
        },
    )

    assert (
        CategoryBinding.objects.filter(
            normalized_title="people",
            released_at__isnull=True,
        ).count()
        == 2
    )
    assert first.pk != second.pk


def test_delete_releases_categories(user):
    """Soft-deleting a page releases its category bindings."""
    page = create_page(
        title="Main Page",
        main_content="Hello",
        author=user,
        properties=properties(["Category:People"]),
    )
    revid = page.current_revision_id
    assert revid is not None
    delete_page(
        page_id=page.pk,
        author=user,
        base_revid=revid,
    )
    assert page.category_bindings.filter(released_at__isnull=True).count() == 0


def test_rebuild_is_idempotent(user):
    """A healthy category projection reports no changes."""
    create_page(
        title="Main Page",
        main_content="Hello",
        author=user,
        properties=properties(["Category:People"]),
    )
    report = rebuild_category_bindings(check_only=True)
    assert report.released == 0
    assert report.created == 0
