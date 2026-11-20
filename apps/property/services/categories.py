"""Category binding synchronization and rebuilds."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.exceptions import InvalidTitle
from apps.core.namespaces import CATEGORY
from apps.core.titles import normalize_title
from apps.property.models.category import CategoryBinding


def _desired_categories(properties: dict) -> dict[str, str]:
    """Return a normalized ``key -> display_title`` map from properties."""
    raw_categories = properties.get("categories", [])
    if not isinstance(raw_categories, list):
        raise InvalidTitle("properties.categories must be a list")
    desired: dict[str, str] = {}
    for raw in raw_categories:
        if not isinstance(raw, str) or not raw.strip():
            raise InvalidTitle("Category titles must be non-empty strings")
        normalized = normalize_title(raw, CATEGORY)
        if normalized.namespace != CATEGORY:
            raise InvalidTitle("Categories must use the Category namespace")
        desired[normalized.key] = normalized.display
    return desired


def sync_category_bindings(*, page, revision, properties: dict) -> None:
    """Reconcile category bindings with a properties object.

    Runs inside the caller's transaction. Removed memberships are released, never
    deleted; new memberships use ``created_revision=revision``. Multiple pages may
    belong to the same category, so there is no cross-page conflict.
    """
    desired = _desired_categories(properties)
    active = list(
        CategoryBinding.objects.select_for_update()
        .filter(page=page, released_at__isnull=True)
        .order_by("id")
    )
    active_by_key = {
        binding.normalized_title: binding for binding in active if binding.namespace == CATEGORY
    }

    now = timezone.now()
    for binding in active:
        wanted = desired.get(binding.normalized_title) if binding.namespace == CATEGORY else None
        if wanted is None or wanted != binding.display_title:
            binding.released_at = now
            binding.released_revision = revision
            binding.save(update_fields=["released_at", "released_revision"])

    for key, display_title in desired.items():
        existing = active_by_key.get(key)
        if existing is not None and existing.released_at is None:
            continue
        try:
            with transaction.atomic():
                CategoryBinding.objects.create(
                    page=page,
                    namespace=CATEGORY,
                    display_title=display_title,
                    normalized_title=key,
                    created_revision=revision,
                )
        except IntegrityError as exc:
            raise InvalidTitle("This page already has an active binding for that category") from exc


@dataclass
class CategoryRebuildReport:
    """Counts produced by a category binding rebuild."""

    pages_scanned: int = 0
    released: int = 0
    created: int = 0


def rebuild_category_bindings(*, check_only: bool = False) -> CategoryRebuildReport:
    """Rebuild category bindings from every live page's current revision."""
    from apps.core.models.page import Page
    from apps.core.services.revisions import get_revision_state

    report = CategoryRebuildReport()
    pages = (
        Page.objects.filter(is_deleted=False)
        .exclude(current_revision__isnull=True)
        .select_related("current_revision")
    )
    for page in pages.iterator():
        report.pages_scanned += 1
        revision = page.current_revision
        if revision is None:
            continue
        state = get_revision_state(revision)
        properties = state["properties"].as_json()
        desired = _desired_categories(properties)

        active = list(page.category_bindings.filter(released_at__isnull=True))
        active_keys = {
            binding.normalized_title for binding in active if binding.namespace == CATEGORY
        }
        to_release = {
            binding.normalized_title
            for binding in active
            if binding.namespace != CATEGORY
            or binding.normalized_title not in desired
            or desired[binding.normalized_title] != binding.display_title
        }
        to_create = {key for key in desired if key not in active_keys or key in to_release}

        report.released += len(to_release)
        report.created += len(to_create)
        if not check_only:
            with transaction.atomic():
                sync_category_bindings(
                    page=page,
                    revision=revision,
                    properties=properties,
                )

    return report
