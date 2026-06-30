from django.apps import AppConfig


class ApiKeysConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.apikeys"
    label = "apikeys"

    def ready(self):
        # Register the drf-spectacular auth extension.
        from . import schema  # noqa: F401
