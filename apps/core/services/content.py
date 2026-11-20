"""Content canonicalization, validation and deduplication."""

from __future__ import annotations

import copy
import hashlib
import json

from django.db import IntegrityError, transaction

from apps.core.constants import ContentModel
from apps.core.exceptions import ContentHashCollision, ContentValidationError
from apps.core.models.content import Content
from apps.core.titles import normalize_title


def canonicalize(value, content_model: str) -> str:
    """Serialize content into its canonical text form.

    JSON is serialized with sorted keys and compact separators so identical objects
    hash identically on SQLite and PostgreSQL.
    """
    if content_model == ContentModel.JSON:
        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ContentValidationError("Properties must be valid JSON") from exc
    if not isinstance(value, str):
        raise ContentValidationError("Text content must be a string")
    return value


def content_sha1(serialized: str) -> str:
    """Return the SHA-1 hex digest of UTF-8 encoded canonical text."""
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def get_or_create_content(content_model: str, value) -> tuple[Content, bool]:
    """Return an existing or newly created ``Content`` row.

    Returns:
        A ``(content, created)`` tuple. ``created`` is true when a new row was
        inserted.

    Raises:
        ContentHashCollision: If an existing row with the same hash has different data.
    """
    serialized = canonicalize(value, content_model)
    digest = content_sha1(serialized)
    size = len(serialized.encode("utf-8"))

    existing = Content.objects.filter(content_model=content_model, sha1=digest).first()
    if existing is not None:
        if existing.data != serialized:
            raise ContentHashCollision(details={"content_model": content_model, "sha1": digest})
        return existing, False

    try:
        with transaction.atomic():
            content = Content.objects.create(
                content_model=content_model,
                data=serialized,
                sha1=digest,
                size=size,
            )
        return content, True
    except IntegrityError:
        existing = Content.objects.get(content_model=content_model, sha1=digest)
        if existing.data != serialized:
            raise ContentHashCollision(details={"content_model": content_model, "sha1": digest})
        return existing, False


def validate_properties(value) -> dict:
    """Validate and return a properties object.

    The full object is validated on every property edit; titles are not merged
    partially. Unknown top-level keys are preserved for forward compatibility.
    """
    if not isinstance(value, dict):
        raise ContentValidationError("Properties must be a JSON object")
    if value.get("schema") != 1:
        raise ContentValidationError("Unsupported properties schema")

    titles = value.get("titles")
    if not isinstance(titles, dict):
        raise ContentValidationError("properties.titles must be an object")

    primary = titles.get("primary")
    if not isinstance(primary, str) or not primary.strip():
        raise ContentValidationError("properties.titles.primary is required")

    aliases = titles.get("aliases", [])
    if not isinstance(aliases, list) or any(not isinstance(item, str) for item in aliases):
        raise ContentValidationError("properties.titles.aliases must be a list of strings")

    primary_norm = normalize_title(primary)
    seen = {primary_norm.key}
    for alias in aliases:
        alias_norm = normalize_title(alias)
        if alias_norm.key == primary_norm.key:
            raise ContentValidationError("An alias cannot equal the primary title")
        if alias_norm.key in seen:
            raise ContentValidationError("Duplicate alias after title normalization")
        seen.add(alias_norm.key)

    redirect = value.get("redirect")
    if redirect is not None:
        if not isinstance(redirect, dict):
            raise ContentValidationError("properties.redirect must be an object or null")
        target = redirect.get("target_page_id")
        if not isinstance(target, int) or target <= 0:
            raise ContentValidationError("properties.redirect.target_page_id is required")

    categories = value.get("categories", [])
    if not isinstance(categories, list) or any(not isinstance(item, str) for item in categories):
        raise ContentValidationError("properties.categories must be a list of strings")

    infobox = value.get("infobox", {})
    if not isinstance(infobox, dict):
        raise ContentValidationError("properties.infobox must be an object")

    return value


def default_properties(primary_title: str) -> dict:
    """Return the standard properties object for a new page."""
    return {
        "schema": 1,
        "titles": {"primary": primary_title, "aliases": []},
        "redirect": None,
        "categories": [],
        "infobox": {},
    }


def copy_properties(value: dict) -> dict:
    """Return a deep copy of a properties object."""
    return copy.deepcopy(value)
