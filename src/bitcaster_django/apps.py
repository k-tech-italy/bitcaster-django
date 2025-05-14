"""bitcaster-django app config."""

from django.apps import AppConfig
from typing_extensions import override


class Config(AppConfig):  # noqa: D101
    verbose_name = "bitcaster-django"
    name = "bitcaster_django"

    @override
    def ready(self) -> None:
        from . import checks  # noqa
        from . import signals  # noqa
