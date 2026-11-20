"""Immutable, content-addressed revision content."""

import json

from django.db import models

from apps.core.constants import ContentModel


class Content(models.Model):
    """An immutable content blob shared by one or more revision slots.

    ``data`` is canonical text: raw text for text models and canonical JSON text for
    JSON models. Storing canonical text instead of a database JSON field keeps hashing
    deterministic across SQLite and PostgreSQL.
    """

    content_model = models.CharField(max_length=32, choices=ContentModel.choices)
    data = models.TextField()
    sha1 = models.CharField(max_length=40)
    size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Content"
        verbose_name_plural = "Content"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_model", "sha1"],
                name="uniq_content_model_sha1",
            ),
        ]

    def __str__(self):
        return f"{self.content_model}:{self.sha1[:12]}"

    @property
    def is_json(self) -> bool:
        """Return whether this content is a JSON document."""
        return self.content_model == ContentModel.JSON

    def as_json(self):
        """Parse and return JSON content.

        Raises:
            ValueError: If this content is not a JSON document.
        """
        if not self.is_json:
            raise ValueError(f"Content {self.pk} is not JSON")
        return json.loads(self.data)

    @property
    def text(self) -> str:
        """Return the raw canonical text."""
        return self.data
