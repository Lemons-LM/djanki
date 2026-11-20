"""Revision slots: named content roles within a revision."""

from django.db import models

from apps.core.constants import SlotRole


class RevisionSlot(models.Model):
    """A named content role in a revision.

    A revision has exactly one ``main`` and one ``properties`` slot. The invariant is
    enforced by the revision service because it spans multiple rows.
    """

    revision = models.ForeignKey(
        "Revision",
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name="Revision",
    )
    role = models.CharField(max_length=32, choices=SlotRole.choices)
    content = models.ForeignKey(
        "Content",
        on_delete=models.PROTECT,
        related_name="slots",
        verbose_name="Content",
    )

    class Meta:
        verbose_name = "Revision slot"
        verbose_name_plural = "Revision slots"
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "role"],
                name="uniq_revision_slot_role",
            ),
        ]

    def __str__(self):
        return f"{self.revision_id}:{self.role}"
