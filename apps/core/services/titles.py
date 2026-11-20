"""Title binding synchronization and resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.exceptions import (
    InvalidTitle,
    PageNotFound,
    RedirectLoop,
    RevisionStateError,
    TitleConflict,
)
from apps.core.models.page import Page
from apps.core.models.title_binding import TitleBinding
from apps.core.titles import NormalizedTitle, normalize_title


@dataclass
class TitleResolution:
    """The result of resolving a raw title to a page and canonical binding."""

    requested: NormalizedTitle
    page: Page
    binding: TitleBinding
    canonical_binding: TitleBinding
    is_alias: bool
    redirect_chain: list[int] = field(default_factory=list)

    @property
    def is_redirect(self) -> bool:
        """Return whether resolving the title crossed a redirect page."""
        return bool(self.redirect_chain)


def _desired_titles(properties: dict, namespace: int) -> dict[str, dict]:
    """Build the desired normalized title map from a properties object."""
    titles = properties.get("titles") or {}
    primary_raw = titles.get("primary")
    if not isinstance(primary_raw, str) or not primary_raw.strip():
        raise InvalidTitle("A primary title is required")

    primary = normalize_title(primary_raw, namespace)
    if primary.namespace != namespace:
        raise InvalidTitle("The primary title must be in the page namespace")

    desired: dict[str, dict] = {
        primary.key: {"display": primary.display, "is_primary": True},
    }
    aliases = titles.get("aliases") or []
    if not isinstance(aliases, list):
        raise InvalidTitle("Aliases must be a list")

    for raw in aliases:
        if not isinstance(raw, str) or not raw.strip():
            raise InvalidTitle("An alias must be a non-empty string")
        alias = normalize_title(raw, namespace)
        if alias.namespace != namespace:
            raise InvalidTitle("An alias must be in the page namespace")
        if alias.key == primary.key:
            raise InvalidTitle("An alias cannot equal the primary title")
        if alias.key in desired:
            raise InvalidTitle("Duplicate alias after title normalization")
        desired[alias.key] = {"display": alias.display, "is_primary": False}

    return desired


def sync_title_bindings(*, page: Page, revision, properties: dict) -> None:
    """Reconcile title bindings with a properties object.

    Runs inside the caller's transaction. Removed or changed bindings are released,
    never deleted, and new bindings are created with ``created_revision=revision``.
    """
    desired = _desired_titles(properties, page.namespace)
    desired_keys = list(desired)

    active = list(
        TitleBinding.objects.select_for_update()
        .filter(page=page, released_at__isnull=True)
        .order_by("id")
    )
    conflicting = (
        TitleBinding.objects.select_for_update()
        .filter(
            namespace=page.namespace,
            normalized_title__in=desired_keys,
            released_at__isnull=True,
        )
        .exclude(page=page)
        .order_by("id")
        .first()
    )
    if conflicting is not None:
        raise TitleConflict(
            details={
                "namespace": page.namespace,
                "title": conflicting.display_title,
                "conflicting_page_id": conflicting.page_id,
            }
        )

    now = timezone.now()
    active_by_key = {binding.normalized_title: binding for binding in active}

    for key, binding in active_by_key.items():
        wanted = desired.get(key)
        changed = wanted is None or (
            wanted["display"] != binding.display_title or wanted["is_primary"] != binding.is_primary
        )
        if changed:
            binding.released_at = now
            binding.released_revision = revision
            binding.save(update_fields=["released_at", "released_revision"])

    for key, wanted in desired.items():
        existing = active_by_key.get(key)
        if existing is not None and existing.released_at is None:
            continue
        try:
            with transaction.atomic():
                TitleBinding.objects.create(
                    page=page,
                    namespace=page.namespace,
                    display_title=wanted["display"],
                    normalized_title=key,
                    is_primary=wanted["is_primary"],
                    created_revision=revision,
                )
        except IntegrityError as exc:
            raise TitleConflict(
                details={
                    "namespace": page.namespace,
                    "title": wanted["display"],
                }
            ) from exc


def resolve_title(raw_title: str, namespace: int = 0) -> TitleResolution:
    """Resolve a title, alias or redirect to a page.

    Raises:
        PageNotFound: If no active binding or target page exists.
        RedirectLoop: If the redirect chain is cyclic or longer than five hops.
    """
    requested = normalize_title(raw_title, namespace)
    binding = (
        TitleBinding.objects.select_related("page", "page__redirect_target")
        .filter(
            namespace=requested.namespace,
            normalized_title=requested.key,
            released_at__isnull=True,
        )
        .first()
    )
    if binding is None or binding.page.is_deleted:
        raise PageNotFound(details={"title": raw_title})

    current_page = binding.page
    redirect_chain: list[int] = []
    visited: set[int] = set()

    while current_page.redirect_target_id is not None:
        if current_page.id in visited or len(redirect_chain) >= 5:
            raise RedirectLoop(details={"title": raw_title})
        visited.add(current_page.id)
        redirect_chain.append(current_page.id)

        target = current_page.redirect_target
        if target is None or target.is_deleted:
            raise PageNotFound(details={"title": raw_title})
        target_binding = TitleBinding.objects.filter(
            page=target,
            is_primary=True,
            released_at__isnull=True,
        ).first()
        if target_binding is None:
            raise PageNotFound(details={"title": raw_title})
        current_page = target

    canonical_binding = TitleBinding.objects.filter(
        page=current_page,
        is_primary=True,
        released_at__isnull=True,
    ).first()
    if canonical_binding is None:
        raise PageNotFound(details={"title": raw_title})

    return TitleResolution(
        requested=requested,
        page=current_page,
        binding=binding,
        canonical_binding=canonical_binding,
        is_alias=not binding.is_primary,
        redirect_chain=redirect_chain,
    )


@dataclass
class RebuildReport:
    """Counts produced by a title binding rebuild."""

    pages_scanned: int = 0
    released: int = 0
    created: int = 0
    conflicts: int = 0


def rebuild_title_bindings(*, check_only: bool = False) -> RebuildReport:
    """Rebuild the title binding projection from current revisions.

    Deleted pages have all active bindings released. Live pages are resynchronized
    from their current properties revision. Safe to rerun.
    """
    from apps.core.services.revisions import get_revision_state

    report = RebuildReport()
    now = timezone.now()

    for page in Page.objects.filter(is_deleted=True).iterator():
        report.pages_scanned += 1
        active = page.title_bindings.filter(released_at__isnull=True)
        count = active.count()
        if count:
            report.released += count
            if not check_only:
                active.update(released_at=now)

    live_pages = (
        Page.objects.filter(is_deleted=False)
        .exclude(current_revision__isnull=True)
        .select_related("current_revision")
    )
    for page in live_pages.iterator():
        report.pages_scanned += 1
        revision = page.current_revision
        if revision is None:
            continue
        try:
            state = get_revision_state(revision)
            if "properties" not in state:
                raise RevisionStateError("Missing properties slot")
            properties = state["properties"].as_json()
            desired = _desired_titles(properties, page.namespace)
        except InvalidTitle:
            report.conflicts += 1
            continue

        active_bindings = list(page.title_bindings.filter(released_at__isnull=True))
        active_by_key = {binding.normalized_title: binding for binding in active_bindings}
        to_release = [
            key
            for key in active_by_key
            if key not in desired
            or active_by_key[key].display_title != desired[key]["display"]
            or active_by_key[key].is_primary != desired[key]["is_primary"]
        ]
        to_create = [
            key
            for key in desired
            if key not in active_by_key or active_by_key[key].normalized_title in to_release
        ]
        report.released += len(to_release)
        report.created += len(to_create)

        if not check_only:
            try:
                sync_title_bindings(
                    page=page,
                    revision=revision,
                    properties=properties,
                )
            except TitleConflict:
                report.conflicts += 1

    return report
