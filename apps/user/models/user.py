from django.db import models
from django.contrib.auth.models import AbstractUser

class WikiUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    real_name = models.CharField(max_length=100, blank=True)
    is_blocked = models.BooleanField(default=False)
    block_page = models.BigIntegerField(default=None, null=True)
    block_date_start = models.DateTimeField(null=True)
    block_date_end = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ("read", "Can read content"),
            ("edit", "Can edit content"),
            ("move", "Can move pages"),
            ("delete", "Can delete pages"),
            ("protect", "Can protect pages"),
            ("import", "Can import data"),
            ("export", "Can export data"),
            ("block", "Can block users"),
            ("unblock", "Can unblock users"),
            ("email", "Can send email"),
            ("upload", "Can upload files"),
            ("edit-interface", "Can edit interface"),
            ("edit-content-model", "Can edit content model"),
            ("bot", "Is a bot"),
            ("suppress", "Can suppress revisions"),
            ("user-rights", "Can change user rights"),
        ]
