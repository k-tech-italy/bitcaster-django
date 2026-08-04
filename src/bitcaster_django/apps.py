"""bitcaster-django app config."""

import logging

from bitcaster_sdk.client import ctx
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
        """Initialize the bitcaster-sdk client from the ``BITCASTER`` settings dictionary.

        The client class itself is configurable via the CLIENT key: the sdk
        `init()` helper is bypassed because it hardcodes the sync client.
        """
        from .config import app_settings  # noqa: PLC0415

        try:
            client_class = app_settings.client_class
            bae = app_settings.bae.strip()
            if not bae:
                raise ConfigurationError("Set BITCASTER_BAE environment variable")
            ctx.set(client_class(bae, **app_settings.sdk_options()))
        except (ConfigurationError, TypeError, ImportError) as e:
            # reported to the user by the `bitcaster_django.checks` system checks
            logger.warning("bitcaster-sdk client not initialized: %s", e)
