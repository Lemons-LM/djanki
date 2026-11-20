"""Page move, rename and title-swap services."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import (
    ContentValidationError,
    EditConflict,
    InvalidTitle,
    PageNotFound,
    PermissionDenied,
    TitleConflict,
)
from apps.core.models.page import Page
from apps.core.models.title_binding import TitleBinding
from apps.core.permissions import require
from apps.core.services.content import (
    copy_properties,
    get_or_create_content,
)
from apps.core.services.pages import create_page, edit_page
from apps.core.services.revisions import create_revision, get_revision_state
from apps.core.titles import normalize_title
from apps.core.constants import ContentModel


@dataclass
class MoveResult:
    """The revisions and optional redirect produced by a move."""

    page: Page
    revision: object
    old_primary: str
    new_primary: str
    redirect_page: Page | None = None
    target_page: Page | None = None
    target_revision: object | None = None


def _find_conflicting_binding(page: Page, key: str):
    return (
        TitleBinding.objects.select_for_update()
        .filter(
            namespace=page.namespace,
            normalized_title=key,
            released_at__isnull=True,
        )
        .exclude(page=page)
        .select_related("page")
        .first()
    )


def _swap_titles(
    *,
    moved_page: Page,
    target_page: Page,
    new_norm,
    old_norm,
    author,
    reason: str,
) -> MoveResult:
    """Exchange the primary titles of two pages without creating redirects."""
    locked = {
        page.pk: page
        for page in Page.objects.select_for_update()
        .filter(pk__in=[moved_page.pk, target_page.pk])
        .order_by("id")
    }
    moved = locked[moved_page.pk]
    target = locked[target_page.pk]

    require(author, "move", target)
    require(author, "edit", target)
    target_revision_obj = target.current_revision
    if target.is_deleted or target_revision_obj is None:
        raise PageNotFound(details={"page_id": target.pk})

    target_state = get_revision_state(target_revision_obj)
    target_properties = target_state["properties"].as_json()
    target_primary = normalize_title(target_properties["titles"]["primary"], target.namespace)
    if target_primary.key != new_norm.key:
        raise TitleConflict("Swap requires a primary-title conflict")

    moved_revision_obj = moved.current_revision
    if moved_revision_obj is None:
        raise PageNotFound(details={"page_id": moved.pk})

    moved_state = get_revision_state(moved_revision_obj)
    moved_properties = moved_state["properties"].as_json()
    moved_main = moved_state["main"]
    target_main = target_state["main"]

    now = timezone.now()
    for page in (moved, target):
        TitleBinding.objects.filter(
            page=page,
            released_at__isnull=True,
        ).update(
            released_at=now,
            released_revision=page.current_revision_id,
        )

    moved_new_properties = copy_properties(moved_properties)
    moved_new_properties["titles"]["primary"] = new_norm.display
    target_new_properties = copy_properties(target_properties)
    target_new_properties["titles"]["primary"] = old_norm.display

    moved_props_content, _ = get_or_create_content(ContentModel.JSON, moved_new_properties)
    target_props_content, _ = get_or_create_content(ContentModel.JSON, target_new_properties)

    moved_revision = create_revision(
        page=moved,
        author=author,
        main_content=moved_main,
        properties_content=moved_props_content,
        comment=reason,
        base_revid=moved.current_revision_id,
    )
    target_revision = create_revision(
        page=target,
        author=author,
        main_content=target_main,
        properties_content=target_props_content,
        comment=reason,
        base_revid=target.current_revision_id,
    )
    moved.refresh_from_db()
    target.refresh_from_db()

    return MoveResult(
        page=moved,
        revision=moved_revision,
        old_primary=old_norm.display,
        new_primary=new_norm.display,
        target_page=target,
        target_revision=target_revision,
    )


def move_page(
    *,
    page_id: int,
    new_title: str,
    author,
    base_revid: int,
    reason: str = "",
    create_redirect: bool = True,
    conflict_policy: str = "fail",
) -> MoveResult:
    """Move a page to a new primary title.

    ``conflict_policy="fail"`` rejects an occupied title. ``"swap"`` exchanges the
    primary titles of two pages when the conflict is primary-vs-primary.
    """
    if base_revid is None:
        raise ContentValidationError("base_revid is required")
    if conflict_policy not in {"fail", "swap"}:
        raise ContentValidationError("Unknown conflict policy")

    with transaction.atomic():
        try:
            page = Page.objects.select_for_update().get(pk=page_id)
        except Page.DoesNotExist as exc:
            raise PageNotFound(details={"page_id": page_id}) from exc

        require(author, "move", page)
        require(author, "edit", page)
        if page.is_deleted:
            raise PermissionDenied("Cannot move a deleted page")
        if page.redirect_target_id is not None:
            raise InvalidTitle("Cannot move a redirect page")
        current_revision = page.current_revision
        if current_revision is None:
            raise EditConflict("The page has no current revision")
        if page.current_revision_id != base_revid:
            raise EditConflict(
                details={
                    "base_revid": base_revid,
                    "current_revid": page.current_revision_id,
                    "current_slug": current_revision.slug,
                }
            )

        new_norm = normalize_title(new_title, page.namespace)
        if new_norm.namespace != page.namespace:
            raise InvalidTitle("Namespace moves are not supported yet")

        state = get_revision_state(current_revision)
        properties = state["properties"].as_json()
        old_primary = properties["titles"]["primary"]
        old_norm = normalize_title(old_primary, page.namespace)

        conflict = _find_conflicting_binding(page, new_norm.key)
        if conflict is not None:
            if conflict_policy == "swap":
                return _swap_titles(
                    moved_page=page,
                    target_page=conflict.page,
                    new_norm=new_norm,
                    old_norm=old_norm,
                    author=author,
                    reason=reason or f"Swap titles with {conflict.page.primary_title}",
                )
            raise TitleConflict(
                details={
                    "namespace": page.namespace,
                    "title": new_norm.display,
                    "conflicting_page_id": conflict.page_id,
                }
            )

        new_properties = copy_properties(properties)
        new_properties["titles"]["primary"] = new_norm.display
        revision = edit_page(
            page_id=page.pk,
            author=author,
            base_revid=base_revid,
            properties=new_properties,
            comment=reason or f"Moved page to {new_norm.display}",
        )
        page = revision.page
        page.refresh_from_db()

        redirect_page = None
        if create_redirect and new_norm.key != old_norm.key:
            redirect_properties = {
                "schema": 1,
                "titles": {"primary": old_norm.display, "aliases": []},
                "redirect": {"target_page_id": page.pk},
                "categories": [],
                "infobox": {},
            }
            redirect_page = create_page(
                title=old_norm.display,
                main_content=f"#REDIRECT [[{new_norm.full_title}]]",
                author=author,
                properties=redirect_properties,
                namespace=page.namespace,
                comment=reason or f"Redirect from {old_norm.display}",
            )

        return MoveResult(
            page=page,
            revision=revision,
            old_primary=old_norm.display,
            new_primary=new_norm.display,
            redirect_page=redirect_page,
        )
