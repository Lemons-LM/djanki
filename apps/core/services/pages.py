"""Page lifecycle services: create, edit, delete, restore, protect."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.core.constants import (
    ContentModel,
    ProtectionAction,
    ProtectionLevel,
)
from apps.core.exceptions import (
    ContentValidationError,
    EditConflict,
    InvalidTitle,
    PageNotFound,
    PermissionDenied,
    RevisionStateError,
    TitleConflict,
)
from apps.core.models.page import Page
from apps.core.models.protection import PageProtection, ProtectionLog
from apps.core.models.title_binding import TitleBinding
from apps.core.permissions import require
from apps.core.services.content import (
    copy_properties,
    default_properties,
    get_or_create_content,
    validate_properties,
)
from apps.core.services.revisions import create_revision, get_revision_state
from apps.core.services.titles import sync_title_bindings
from apps.core.titles import normalize_title


def _validate_title_set(properties: dict, namespace: int) -> str:
    """Validate that all titles are in the expected namespace and return the primary key."""
    primary = normalize_title(properties["titles"]["primary"], namespace)
    if primary.namespace != namespace:
        raise InvalidTitle("The primary title must be in the page namespace")
    for alias in properties["titles"].get("aliases", []):
        alias_norm = normalize_title(alias, namespace)
        if alias_norm.namespace != namespace:
            raise InvalidTitle("Aliases must be in the page namespace")
    return primary.key


def _raise_if_title_conflict(properties: dict, namespace: int) -> None:
    """Fail fast when any desired title is active on another page."""
    keys = [normalize_title(properties["titles"]["primary"], namespace).key]
    keys.extend(
        normalize_title(alias, namespace).key for alias in properties["titles"].get("aliases", [])
    )
    conflict = (
        TitleBinding.objects.filter(
            namespace=namespace,
            normalized_title__in=keys,
            released_at__isnull=True,
        )
        .select_related("page")
        .first()
    )
    if conflict is not None:
        raise TitleConflict(
            details={
                "namespace": namespace,
                "title": conflict.display_title,
                "conflicting_page_id": conflict.page_id,
            }
        )


def create_page(
    *,
    title: str,
    main_content: str,
    author,
    properties: dict | None = None,
    namespace: int = 0,
    comment: str = "",
    ip: str | None = None,
) -> Page:
    """Create a page and its first revision atomically.

    ``properties`` defaults to a standard object containing ``title`` as the primary
    title. If supplied, its primary title must normalize to the same key as ``title``.
    """
    require(author, "edit")

    normalized = normalize_title(title, namespace)
    if properties is None:
        properties = default_properties(normalized.display)
    else:
        properties = copy_properties(properties)
        validate_properties(properties)

    properties_primary = normalize_title(
        properties["titles"]["primary"],
        normalized.namespace,
    )
    if properties_primary.key != normalized.key:
        raise InvalidTitle("The properties primary title does not match the page title")
    _validate_title_set(properties, normalized.namespace)
    _raise_if_title_conflict(properties, normalized.namespace)

    with transaction.atomic():
        page = Page.objects.create(namespace=normalized.namespace)
        main_object, _ = get_or_create_content(ContentModel.WIKITEXT, main_content)
        properties_object, _ = get_or_create_content(ContentModel.JSON, properties)
        create_revision(
            page=page,
            author=author,
            main_content=main_object,
            properties_content=properties_object,
            comment=comment,
            ip=ip,
        )
        redirect = properties.get("redirect")
        if redirect:
            target_id = redirect["target_page_id"]
            try:
                target = Page.objects.get(pk=target_id)
            except Page.DoesNotExist as exc:
                raise ContentValidationError("Redirect target does not exist") from exc
            if target.pk == page.pk:
                raise ContentValidationError("A page cannot redirect to itself")
            page.redirect_target = target
            page.save(update_fields=["redirect_target", "updated_at"])
        page.refresh_from_db()
        return page


def edit_page(
    *,
    page_id: int,
    author,
    base_revid: int,
    main: str | None = None,
    properties: dict | None = None,
    comment: str = "",
    minor: bool = False,
    bot: bool = False,
    ip: str | None = None,
):
    """Create a new revision for an existing page.

    ``base_revid`` is mandatory. At least one of ``main`` or ``properties`` must be
    supplied; unchanged slots reuse their current content.
    """
    if base_revid is None:
        raise ContentValidationError("base_revid is required")
    if main is None and properties is None:
        raise ContentValidationError("An edit must change main content or properties")

    with transaction.atomic():
        try:
            page = Page.objects.select_for_update().get(pk=page_id)
        except Page.DoesNotExist as exc:
            raise PageNotFound(details={"page_id": page_id}) from exc

        require(author, "edit", page)
        if page.is_deleted or page.is_suppressed:
            raise PermissionDenied("Cannot edit a deleted or suppressed page")
        if page.current_revision_id is None:
            raise RevisionStateError("The page has no current revision")
        if page.current_revision_id != base_revid:
            current = page.current_revision
            raise EditConflict(
                details={
                    "base_revid": base_revid,
                    "current_revid": page.current_revision_id,
                    "current_slug": current.slug if current else None,
                }
            )

        current_revision = page.current_revision
        if current_revision is None:
            raise RevisionStateError("The page has no current revision")
        state = get_revision_state(current_revision)
        current_main = state["main"]
        current_properties = state["properties"]

        if main is None:
            main_object = current_main
        else:
            main_model = (
                current_main.content_model
                if current_main.content_model in (ContentModel.WIKITEXT, ContentModel.TEXT)
                else ContentModel.WIKITEXT
            )
            main_object, _ = get_or_create_content(main_model, main)

        if properties is None:
            properties_object = current_properties
        else:
            properties = copy_properties(properties)
            validate_properties(properties)
            properties_object, _ = get_or_create_content(ContentModel.JSON, properties)

        return create_revision(
            page=page,
            author=author,
            main_content=main_object,
            properties_content=properties_object,
            comment=comment,
            minor=minor,
            bot=bot,
            base_revid=base_revid,
            ip=ip,
        )


def _release_active_projections(page: Page, revision) -> None:
    """Release active title and category bindings for a page."""
    now = timezone.now()
    page.title_bindings.filter(released_at__isnull=True).update(
        released_at=now,
        released_revision=revision,
    )
    page.category_bindings.filter(released_at__isnull=True).update(
        released_at=now,
        released_revision=revision,
    )


def delete_page(*, page_id: int, author, base_revid: int, reason: str = "") -> None:
    """Soft-delete a page and release its titles."""
    if base_revid is None:
        raise ContentValidationError("base_revid is required")
    with transaction.atomic():
        try:
            page = Page.objects.select_for_update().get(pk=page_id)
        except Page.DoesNotExist as exc:
            raise PageNotFound(details={"page_id": page_id}) from exc
        require(author, "delete", page)
        if page.current_revision_id != base_revid:
            current = page.current_revision
            raise EditConflict(
                details={
                    "base_revid": base_revid,
                    "current_revid": page.current_revision_id,
                    "current_slug": current.slug if current else None,
                }
            )
        if not page.is_deleted:
            _release_active_projections(page, page.current_revision)
            page.is_deleted = True
            page.save(update_fields=["is_deleted", "updated_at"])


def restore_page(*, page_id: int, author, base_revid: int, reason: str = "") -> Page:
    """Restore a soft-deleted page and rebuild its title bindings."""
    if base_revid is None:
        raise ContentValidationError("base_revid is required")
    with transaction.atomic():
        try:
            page = Page.objects.select_for_update().get(pk=page_id)
        except Page.DoesNotExist as exc:
            raise PageNotFound(details={"page_id": page_id}) from exc
        require(author, "restore", page)
        if page.current_revision_id != base_revid:
            current = page.current_revision
            raise EditConflict(
                details={
                    "base_revid": base_revid,
                    "current_revid": page.current_revision_id,
                    "current_slug": current.slug if current else None,
                }
            )
        current_revision = page.current_revision
        if current_revision is None:
            raise RevisionStateError("The page has no current revision")
        state = get_revision_state(current_revision)
        properties = state["properties"].as_json()
        sync_title_bindings(
            page=page,
            revision=current_revision,
            properties=properties,
        )
        from apps.property.services.categories import sync_category_bindings

        sync_category_bindings(
            page=page,
            revision=current_revision,
            properties=properties,
        )
        page.is_deleted = False
        page.save(update_fields=["is_deleted", "updated_at"])
        return page


def protect_page(
    *,
    page_id: int,
    author,
    protection: dict[str, str],
    base_revid: int | None = None,
    reason: str = "",
    expires_at=None,
) -> Page:
    """Update structured page protection rows and append a change log.

    ``protection`` maps an action (``edit``/``move``/``delete``/``create``) to a level
    (``open``/``autoconfirmed``/``sysop``). ``expires_at`` applies to every action in
    the request; ``None`` means indefinite.
    """
    if not isinstance(protection, dict):
        raise ContentValidationError("protection must be an object")
    allowed_actions = {action.value for action in ProtectionAction}
    allowed_levels = {level.value for level in ProtectionLevel}
    for action, level in protection.items():
        if action not in allowed_actions:
            raise ContentValidationError(f"Unknown protection action: {action}")
        if level not in allowed_levels:
            raise ContentValidationError(f"Unknown protection level: {level}")
    if expires_at is not None and expires_at <= timezone.now():
        raise ContentValidationError("expires_at must be in the future")

    with transaction.atomic():
        try:
            page = Page.objects.select_for_update().get(pk=page_id)
        except Page.DoesNotExist as exc:
            raise PageNotFound(details={"page_id": page_id}) from exc
        require(author, "protect", page)
        if base_revid is not None and page.current_revision_id != base_revid:
            current = page.current_revision
            raise EditConflict(
                details={
                    "base_revid": base_revid,
                    "current_revid": page.current_revision_id,
                    "current_slug": current.slug if current else None,
                }
            )

        for action, level in protection.items():
            existing = (
                PageProtection.objects.select_for_update().filter(page=page, action=action).first()
            )
            if existing is not None and existing.is_active:
                old_level = existing.level
                old_expires = existing.expires_at
            else:
                old_level = ProtectionLevel.OPEN
                old_expires = None

            if level == ProtectionLevel.OPEN:
                if existing is not None:
                    existing.delete()
            elif existing is None:
                PageProtection.objects.create(
                    page=page,
                    action=action,
                    level=level,
                    expires_at=expires_at,
                    set_by=author,
                    set_by_name=getattr(author, "username", "") or "",
                    reason=reason,
                )
            else:
                existing.level = level
                existing.expires_at = expires_at
                existing.set_by = author
                existing.set_by_name = getattr(author, "username", "") or ""
                existing.set_at = timezone.now()
                existing.reason = reason
                existing.save(
                    update_fields=[
                        "level",
                        "expires_at",
                        "set_by",
                        "set_by_name",
                        "set_at",
                        "reason",
                    ]
                )

            if old_level != level or old_expires != expires_at:
                ProtectionLog.objects.create(
                    page=page,
                    action=action,
                    old_level=old_level,
                    new_level=level,
                    expires_at=expires_at,
                    reason=reason,
                    changed_by=author,
                    changed_by_name=getattr(author, "username", "") or "",
                    revision=page.current_revision,
                )

        page.save(update_fields=["updated_at"])
        return page


def suppress_revision(*, revision_id: int, author, suppressed: bool = True) -> None:
    """Set or clear the suppression flag on a revision."""
    from apps.core.models.revision import Revision

    with transaction.atomic():
        try:
            revision = (
                Revision.objects.select_for_update().select_related("page").get(pk=revision_id)
            )
        except Revision.DoesNotExist as exc:
            raise PageNotFound(details={"revision_id": revision_id}) from exc
        require(author, "suppress", revision.page)
        revision.suppressed = suppressed
        revision.save(update_fields=["suppressed"])
