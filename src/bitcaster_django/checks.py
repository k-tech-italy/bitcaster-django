"""`AppConfig.ready()` checks specific for bitcaster-django."""

import re
from typing import TYPE_CHECKING

from django.core import checks

if TYPE_CHECKING:
    from django.apps import AppConfig

from bitcaster_sdk.client import Client

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
        if not re.match(Client.url_regex, url):
            messages.append(
                checks.Error(
                    f"'{bae}' is not a valid Bitcaster BAE.",
                    hint="The BAE must match 'https://<token>@<host>/api/o/<organization>/'.",
                    id="bitcaster_django.E002",
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
