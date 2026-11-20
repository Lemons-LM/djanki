"""Revision creation and state helpers."""

from __future__ import annotations

from django.db import transaction

from apps.core.constants import ContentModel, SlotRole
from apps.core.exceptions import (
    ContentValidationError,
    EditConflict,
    InvalidRevisionSlug,
    RevisionNotFound,
    RevisionStateError,
)
from apps.core.models.content import Content
from apps.core.models.page import Page
from apps.core.models.revision import Revision
from apps.core.models.slot import RevisionSlot
from apps.core.services.titles import sync_title_bindings


def get_revision_state(revision: Revision) -> dict[str, Content]:
    """Return the ``role -> Content`` map for a revision.

    Raises:
        RevisionStateError: If the revision does not have exactly the required roles.
    """
    slots = {slot.role: slot.content for slot in revision.slots.select_related("content")}
    required = {"main", "properties"}
    if set(slots) != required:
        raise RevisionStateError(details={"revision_id": revision.pk, "roles": sorted(slots)})
    return slots


def create_revision(
    *,
    page: Page,
    author,
    main_content: Content,
    properties_content: Content,
    comment: str = "",
    minor: bool = False,
    bot: bool = False,
    base_revid: int | None = None,
    ip: str | None = None,
) -> Revision:
    """Create a complete revision and update the page's current pointer.

    The revision always has both ``main`` and ``properties`` slots. Callers pass
    reusable ``Content`` objects; unchanged slots should reuse the current content.

    Raises:
        EditConflict: If ``base_revid`` does not match the page's current revision.
        ContentValidationError: If the properties content is not JSON.
    """
    if properties_content.content_model != ContentModel.JSON:
        raise ContentValidationError("The properties slot must use the JSON content model")

    with transaction.atomic():
        page = Page.objects.select_for_update().get(pk=page.pk)

        if base_revid is not None and page.current_revision_id != base_revid:
            current = page.current_revision
            raise EditConflict(
                details={
                    "base_revid": base_revid,
                    "current_revid": page.current_revision_id,
                    "current_slug": current.slug if current else None,
                }
            )

        next_number = page.revision_count + 1
        parent = page.current_revision
        revision = Revision.objects.create(
            page=page,
            page_rev_number=next_number,
            parent_revision=parent,
            author=author,
            author_name=getattr(author, "username", "") or "",
            author_ip=ip,
            comment=comment,
            minor=minor,
            bot=bot,
        )
        RevisionSlot.objects.create(
            revision=revision,
            role=SlotRole.MAIN,
            content=main_content,
        )
        RevisionSlot.objects.create(
            revision=revision,
            role=SlotRole.PROPERTIES,
            content=properties_content,
        )

        page.current_revision = revision
        page.revision_count = next_number
        page.save(update_fields=["current_revision", "revision_count", "updated_at"])

        properties = properties_content.as_json()
        sync_title_bindings(
            page=page,
            revision=revision,
            properties=properties,
        )
        from apps.property.services.categories import sync_category_bindings

        sync_category_bindings(
            page=page,
            revision=revision,
            properties=properties,
        )

        return revision


def resolve_revision(value) -> Revision:
    """Resolve a global revid or a ``p{page_id}-r{number}`` slug.

    Raises:
        InvalidRevisionSlug: If the value is neither an integer nor a valid slug.
        RevisionNotFound: If the revision does not exist.
    """
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        try:
            return Revision.objects.select_related("page").get(pk=int(value))
        except Revision.DoesNotExist as exc:
            raise RevisionNotFound(details={"revid": value}) from exc

    parsed = Revision.parse_slug(str(value))
    if parsed is None:
        raise InvalidRevisionSlug(details={"value": value})
    page_id, number = parsed
    try:
        return Revision.objects.select_related("page").get(
            page_id=page_id,
            page_rev_number=number,
        )
    except Revision.DoesNotExist as exc:
        raise RevisionNotFound(details={"value": value}) from exc
