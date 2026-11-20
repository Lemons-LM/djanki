"""Test settings for PostgreSQL CI.

The default test configuration uses SQLite through ``config.settings.dev``. This module
is used by the PostgreSQL CI job and can also be used locally with a running database.
"""

import os

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "test-secret-key")
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "djanki"),
        "USER": os.environ.get("DB_USER", "djanki"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "djanki"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
