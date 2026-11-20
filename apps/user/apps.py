from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user"
    verbose_name = "Users"

    def ready(self):
        """Register post-migrate group seeding."""
        from . import groups  # noqa: F401
