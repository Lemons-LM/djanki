"""Read-only query helpers used by the API and admin."""

from __future__ import annotations

from django.core.paginator import Paginator

from apps.core.exceptions import PageNotFound
from apps.core.models.page import Page
from apps.core.models.title_binding import TitleBinding
from apps.core.services.revisions import resolve_revision


def get_page(page_id: int) -> Page:
    """Return a page or raise ``PageNotFound``."""
    try:
        return Page.objects.get(pk=page_id)
    except Page.DoesNotExist as exc:
        raise PageNotFound(details={"page_id": page_id}) from exc


def get_page_for_read(page_id: int) -> Page:
    """Return a page with the relations needed for rendering."""
    try:
        return Page.objects.select_related("current_revision", "redirect_target").get(pk=page_id)
    except Page.DoesNotExist as exc:
        raise PageNotFound(details={"page_id": page_id}) from exc


def get_revision(value):
    """Resolve a revid or slug and prefetch its slots."""
    revision = resolve_revision(value)
    return RevisionWithSlots(revision)


def page_history(page: Page, *, page_number: int = 1, page_size: int = 50):
    """Return a paginated revision history for a page."""
    queryset = (
        page.revisions.select_related("author")
        .prefetch_related("slots__content")
        .order_by("-page_rev_number")
    )
    return Paginator(queryset, page_size).get_page(page_number)


def get_active_binding(namespace: int, normalized_title: str) -> TitleBinding | None:
    """Return the active binding for a title, if any."""
    return (
        TitleBinding.objects.select_related("page", "page__redirect_target")
        .filter(
            namespace=namespace,
            normalized_title=normalized_title,
            released_at__isnull=True,
        )
        .first()
    )


def title_binding_history(normalized_title: str, *, namespace: int = 0):
    """Return all binding intervals for a title, newest first."""
    return (
        TitleBinding.objects.select_related("page", "created_revision")
        .filter(namespace=namespace, normalized_title=normalized_title)
        .order_by("-created_at")
    )


class RevisionWithSlots:
    """Small wrapper that prefetches slots and content for a revision."""

    def __init__(self, revision):
        self.revision = revision
        self.slots = {slot.role: slot.content for slot in revision.slots.select_related("content")}

    @property
    def state(self) -> dict:
        """Return the ``role -> Content`` map."""
        return self.slots
