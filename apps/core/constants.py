"""Shared constants for the core app."""

from django.db import models


class ContentModel(models.TextChoices):
    """Supported content models for a revision slot."""

    WIKITEXT = "wikitext", "Wikitext"
    TEXT = "text", "Plain text"
    JSON = "json", "JSON"
    CSS = "css", "CSS"
    JS = "js", "JavaScript"


class SlotRole(models.TextChoices):
    """Well-known revision slot roles."""

    MAIN = "main", "Main"
    PROPERTIES = "properties", "Properties"


class ProtectionLevel(models.TextChoices):
    """Page protection levels."""

    OPEN = "open", "Open"
    AUTOCONFIRMED = "autoconfirmed", "Autoconfirmed"
    SYSOP = "sysop", "Sysop"


class ProtectionAction(models.TextChoices):
    """Page actions that can be protected."""

    EDIT = "edit", "Edit"
    MOVE = "move", "Move"
    DELETE = "delete", "Delete"
    CREATE = "create", "Create"
