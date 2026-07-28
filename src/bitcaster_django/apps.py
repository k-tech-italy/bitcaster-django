"""bitcaster-django app config."""

from django.apps import AppConfig


class Config(AppConfig):  # noqa: D101
    verbose_name = "bitcaster-django"
    name = "bitcaster_django"

    def ready(self) -> None:
        """Import checks module when the app is ready."""
        from . import checks  # noqa
        from . import signals  # noqa
