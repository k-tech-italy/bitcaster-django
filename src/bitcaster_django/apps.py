"""bitcaster-django app config."""

import logging

import bitcaster_sdk
from bitcaster_sdk.exceptions import ConfigurationError
from django.apps import AppConfig
from typing_extensions import override

logger = logging.getLogger(__name__)


class Config(AppConfig):  # noqa: D101
    verbose_name = "bitcaster-django"
    name = "bitcaster_django"

    @override
    def ready(self) -> None:
        from . import checks, handlers  # noqa: F401, PLC0415

        self.init_sdk()

    def init_sdk(self) -> None:
        """Initialize the bitcaster-sdk client from the ``BITCASTER`` settings dictionary."""
        from .config import app_settings  # noqa: PLC0415

        try:
            bitcaster_sdk.init(app_settings.bae, **app_settings.sdk_options())
        except (ConfigurationError, TypeError) as e:
            # reported to the user by the `bitcaster_django.checks` system checks
            logger.warning("bitcaster-sdk client not initialized: %s", e)
