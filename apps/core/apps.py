from django.apps import AppConfig


class PageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.core"
    def ready(self):
        import apps.core.signals
