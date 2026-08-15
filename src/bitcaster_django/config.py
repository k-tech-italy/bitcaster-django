"""Access to the ``BITCASTER`` settings dictionary."""

import os
from typing import TYPE_CHECKING, Any

from django.apps import apps
from django.conf import settings
from django.utils.module_loading import import_string


if TYPE_CHECKING:
    from bitcaster_sdk.abstract_client import AbstractClient


#: name of the dictionary in the Django settings holding the bitcaster configuration
SETTINGS_KEY = "BITCASTER"

DEFAULTS: dict[str, Any] = {
    # Bitcaster Application Endpoint. Falls back to the BITCASTER_BAE environment variable.
    "BAE": "",
    # forwarded to the sdk client
    "DEBUG": False,
    # keep Bitcaster users aligned with Django users (post_save handler)
    "SYNC_USERS": True,
    # Bitcaster project slug used to trigger events.
    # Falls back to the BITCASTER_PROJECT_SLUG environment variable.
    "PROJECT": "",
    # Bitcaster application slug used to trigger events.
    # Falls back to the BITCASTER_APPLICATION environment variable.
    "APPLICATION": "",
    # Bitcaster distribution list synced users are added to (optional).
    # Falls back to the BITCASTER_DISTRIBUTION_LIST environment variable.
    "DISTRIBUTION_LIST": "",
    # fully qualified name of the sdk client class to instantiate at startup
    # (e.g. "bitcaster_sdk.async_client.AsyncClient")
    "CLIENT": "bitcaster_sdk.client.Client",
}

#: keys consumed by bitcaster-django itself, never forwarded to the sdk client
APP_ONLY_KEYS = ("BAE", "SYNC_USERS", "PROJECT", "APPLICATION", "DISTRIBUTION_LIST", "CLIENT")


def get_user_settings() -> dict[str, Any]:
    """Return the ``BITCASTER`` dictionary as defined in the Django settings."""
    return getattr(settings, SETTINGS_KEY, {})


def get_constance_value(name: str) -> Any:  # noqa: ANN401
    """Return the runtime value of the ``BITCASTER_<name>`` django-constance key, if available.

    Returns None when constance is not installed, the key is not declared in
    ``CONSTANCE_CONFIG``, or its backend is not ready (e.g. before migrations).
    """
    # `apps.ready` is False during `AppConfig.ready()`: avoid hitting the
    # constance backend (usually the database) while Django is starting up.
    if not apps.ready or "constance" not in settings.INSTALLED_APPS:
        return None
    try:
        from constance import config  # noqa: PLC0415

        return getattr(config, f"{SETTINGS_KEY}_{name}")
    except Exception:  # noqa: BLE001  # missing key, backend/database not ready...
        return None


class AppSettings:
    """Lazy proxy over the bitcaster-django configuration, applying ``DEFAULTS``.

    Resolution order: django-constance ``BITCASTER_<KEY>`` key (optional, when
    non-empty) -> ``BITCASTER`` settings dictionary -> ``DEFAULTS``.
    """

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        if name not in DEFAULTS:
            raise AttributeError(name)
        value = get_constance_value(name)
        if value is None or value == "":
            value = get_user_settings().get(name, DEFAULTS[name])
        return value

    @property
    def bae(self) -> str:
        """Return the configured BAE, falling back to the BITCASTER_BAE environment variable."""
        return self.BAE or os.environ.get("BITCASTER_BAE", "")

    @property
    def project(self) -> str:
        """Return the project slug, falling back to the BITCASTER_PROJECT_SLUG environment variable."""
        return self.PROJECT or os.environ.get("BITCASTER_PROJECT_SLUG", "")

    @property
    def application(self) -> str:
        """Return the application slug, falling back to the BITCASTER_APPLICATION environment variable."""
        return self.APPLICATION or os.environ.get("BITCASTER_APPLICATION", "")

    @property
    def distribution_list(self) -> str:
        """Return the distribution list name, falling back to the BITCASTER_DISTRIBUTION_LIST environment variable."""
        return self.DISTRIBUTION_LIST or os.environ.get("BITCASTER_DISTRIBUTION_LIST", "")

    @property
    def client_class(self) -> "type[AbstractClient]":
        """Return the sdk client class configured via the CLIENT fully qualified class name.

        Raises ImportError when the configured name cannot be imported.
        """
        return import_string(self.CLIENT)

    def sdk_options(self) -> dict[str, Any]:
        """Return the options to forward to the sdk client as lowercase kwargs."""
        merged = {**DEFAULTS, **get_user_settings()}
        return {k.lower(): v for k, v in merged.items() if k not in APP_ONLY_KEYS}


app_settings = AppSettings()
