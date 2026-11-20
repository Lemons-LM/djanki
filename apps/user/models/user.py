from django.contrib.auth.models import AbstractUser
from django.db import models


class WikiUser(AbstractUser):
    """Custom wiki user.

    Block state is stored in the related ``Block`` history, not as inline fields.
    """

    phone = models.CharField(max_length=20, blank=True)
    real_name = models.CharField(max_length=100, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ("block_user", "Can block users"),
            ("unblock_user", "Can unblock users"),
            ("change_user_rights", "Can change user rights"),
            ("send_email", "Can send email"),
            ("bot", "Is a bot"),
        ]

    @property
    def is_currently_blocked(self) -> bool:
        """Return whether the user has an active block."""
        if not self.pk:
            return False
        from apps.user.models.block import Block

        return Block.active_for(self).exists()
