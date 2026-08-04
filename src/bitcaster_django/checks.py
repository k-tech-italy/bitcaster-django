"""`AppConfig.ready()` checks specific for bitcaster-django."""

import re
from typing import TYPE_CHECKING

from django.core import checks


if TYPE_CHECKING:
    from django.apps import AppConfig

from bitcaster_sdk.abstract_client import AbstractClient

from .config import DEFAULTS, SETTINGS_KEY, app_settings, get_user_settings


@checks.register("bitcaster")
def check_bitcaster_settings(app_configs: "list[AppConfig] | None", **kwargs: object) -> list[checks.CheckMessage]:
    """Validate the ``BITCASTER`` settings dictionary."""
    messages: list[checks.CheckMessage] = []
    bae = app_settings.bae
    if not bae:
        messages.append(
            checks.Error(
                "Bitcaster BAE is not configured.",
                hint=f'Set {SETTINGS_KEY} = {{"BAE": "https://<token>@<host>/api/o/<organization>/"}} '
                f"in your settings, or the BITCASTER_BAE environment variable.",
                id="bitcaster_django.E001",
            )
        )
    else:
        url = bae if bae.endswith("/") else f"{bae}/"
        if not re.match(AbstractClient.url_regex, url):
            messages.append(
                checks.Error(
                    f"'{bae}' is not a valid Bitcaster BAE.",
                    hint="The BAE must match 'https://<token>@<host>/api/o/<organization>/'.",
                    id="bitcaster_django.E002",
                )
            )
    client_error = ""
    try:
        client_class = app_settings.client_class
        if not (isinstance(client_class, type) and issubclass(client_class, AbstractClient)):
            client_error = f"'{app_settings.CLIENT}' is not a bitcaster-sdk client class."
    except ImportError:
        client_error = f"Cannot import '{app_settings.CLIENT}'."
    if client_error:
        messages.append(
            checks.Error(
                client_error,
                hint="CLIENT must be the fully qualified name of a "
                "'bitcaster_sdk.abstract_client.AbstractClient' subclass, "
                "e.g. 'bitcaster_sdk.client.Client' or 'bitcaster_sdk.async_client.AsyncClient'.",
                id="bitcaster_django.E003",
            )
        )
    messages.extend(
        checks.Warning(
            f"Unknown key '{key}' in the {SETTINGS_KEY} setting.",
            hint=f"Valid keys are: {', '.join(sorted(DEFAULTS))}.",
            id="bitcaster_django.W001",
        )
        for key in get_user_settings()
        if key not in DEFAULTS
    )
    return messages
