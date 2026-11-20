"""Tests for moves, redirects and title swaps."""

import pytest

from apps.core.exceptions import TitleConflict
from apps.core.services.moves import move_page
from apps.core.services.pages import create_page
from apps.core.services.titles import resolve_title

pytestmark = pytest.mark.django_db


def test_move_creates_redirect(user, page):
    """A rename creates a redirect page and the old title resolves through it."""
    result = move_page(
        page_id=page.pk,
        new_title="New Main Page",
        author=user,
        base_revid=page.current_revision_id,
    )

    assert result.redirect_page is not None
    resolution = resolve_title("Main Page")
    assert resolution.is_redirect is True
    assert resolution.page.pk == page.pk
    assert resolution.canonical_binding.display_title == "New Main Page"


def test_move_to_occupied_title_fails(user, page):
    """A normal move does not steal an occupied primary title."""
    other = create_page(title="Other Page", main_content="Other", author=user)

    with pytest.raises(TitleConflict):
        move_page(
            page_id=page.pk,
            new_title="Other Page",
            author=user,
            base_revid=page.current_revision_id,
            conflict_policy="fail",
        )
    assert other.pk != page.pk


def test_swap_exchanges_primary_titles(user, page):
    """Swap mode exchanges the primary titles of two pages."""
    other = create_page(title="Other Page", main_content="Other", author=user)

    result = move_page(
        page_id=page.pk,
        new_title="Other Page",
        author=user,
        base_revid=page.current_revision_id,
        conflict_policy="swap",
    )

    page.refresh_from_db()
    other.refresh_from_db()
    assert result.target_page is not None
    assert result.target_page.pk == other.pk
    assert page.primary_title == "Other Page"
    assert other.primary_title == "Main Page"
