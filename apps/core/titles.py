"""Title normalization shared by services, URLs and the API.

Normalization is done in Python rather than with database collation so SQLite and
PostgreSQL behave identically.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from apps.core.exceptions import InvalidTitle
from apps.core.namespaces import (
    FIRST_LETTER_CASE_NAMESPACES,
    MAIN,
    NAMESPACE_NAMES,
    namespace_name,
)

FORBIDDEN_CHARS = set("#<>[]|{}")
MAX_TITLE_CHARS = 255
MAX_TITLE_BYTES = 255

# Longest prefix first so "User talk:" wins over "User:".
_NAMESPACE_PREFIXES = sorted(
    ((f"{name}:".casefold(), number) for number, name in NAMESPACE_NAMES.items() if name),
    key=lambda item: len(item[0]),
    reverse=True,
)


@dataclass(frozen=True)
class NormalizedTitle:
    """A namespace, a display title and a normalized uniqueness key."""

    namespace: int
    display: str
    key: str

    @property
    def full_title(self) -> str:
        """Return the namespace-prefixed display title."""
        prefix = namespace_name(self.namespace)
        return f"{prefix}:{self.display}" if prefix else self.display


def _split_namespace(raw: str, default_namespace: int) -> tuple[int, str]:
    if raw.startswith(":"):
        return MAIN, raw[1:]
    folded = raw.casefold()
    for prefix, number in _NAMESPACE_PREFIXES:
        if folded.startswith(prefix):
            return number, raw[len(prefix) :]
    return default_namespace, raw


def normalize_title(raw: str, namespace: int | None = None) -> NormalizedTitle:
    """Normalize a raw title.

    Args:
        raw: User-supplied title, optionally with a known namespace prefix.
        namespace: Default namespace when the title has no prefix.

    Raises:
        InvalidTitle: If the title is empty, contains forbidden characters, or is too
            long in characters or UTF-8 bytes.
    """
    if not isinstance(raw, str):
        raise InvalidTitle("Title must be a string")
    raw = raw.strip()
    if not raw:
        raise InvalidTitle("Title must not be empty")

    default_namespace = MAIN if namespace is None else namespace
    namespace_value, title = _split_namespace(raw, default_namespace)

    title = unicodedata.normalize("NFC", title).replace("_", " ")
    title = " ".join(title.split())
    if not title:
        raise InvalidTitle("Title must not be empty")
    if any(char in FORBIDDEN_CHARS for char in title):
        raise InvalidTitle("Title contains a forbidden character")
    if any(ord(char) < 32 for char in title):
        raise InvalidTitle("Title contains a control character")

    if namespace_value in FIRST_LETTER_CASE_NAMESPACES and title:
        title = title[0].upper() + title[1:]

    key = unicodedata.normalize("NFC", title).casefold()
    if len(key) > MAX_TITLE_CHARS:
        raise InvalidTitle("Title is too long")
    if len(key.encode("utf-8")) > MAX_TITLE_BYTES:
        raise InvalidTitle("Title is too long in UTF-8 bytes")

    return NormalizedTitle(namespace=namespace_value, display=title, key=key)
