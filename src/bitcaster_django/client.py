"""Client module for interacting with Bitcaster.

Defines a `Client` facade over the bitcaster-sdk client initialized at
startup by `bitcaster_django.apps.Config.ready()`: it maps local event names
(`EventConfig`) to remote Bitcaster events and wraps the sdk user management
API. All Bitcaster calls made by the application should go through this class.
"""

import urllib.parse
from typing import Any

import requests
from bitcaster_sdk.client import Client as SdkClient
from bitcaster_sdk.client import ctx
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404

from bitcaster_django.config import SETTINGS_KEY, app_settings
from bitcaster_django.models import EventConfig


class Client:
    """
    Facade over the bitcaster-sdk client for triggering remote events and managing users.

    Relies on the sdk client initialized at startup from the ``BITCASTER``
    settings dictionary; uses local event configuration stored in the database
    to map local event names to remote Bitcaster event slugs.
    """

    def __init__(self) -> None:
        if ctx.get().transport is None:
            raise ImproperlyConfigured(
                f"The bitcaster-sdk client is not initialized: check the {SETTINGS_KEY} setting."
            )

    @property
    def sdk(self) -> SdkClient:
        """Return the bitcaster-sdk client initialized at startup."""
        return ctx.get()

    def trigger_event(self, event_name: str, context: "dict[str, str] | None" = None, **kwargs: Any) -> Any:  # noqa: ANN401
        """Trigger the remote Bitcaster event mapped to the given local event name."""
        mapping = get_object_or_404(EventConfig, local_name=event_name)
        project = app_settings.project
        application = app_settings.application
        if not project:
            raise ImproperlyConfigured(f"Missing PROJECT in the {SETTINGS_KEY} setting.")
        if not application:
            raise ImproperlyConfigured(f"Missing APPLICATION in the {SETTINGS_KEY} setting.")
        return self.sdk.trigger(
            project=project, application=application, event=mapping.remote_event_slug, context=context, **kwargs
        )

    def add_user(self, email: str, first_name: str = "", last_name: str = "") -> Any:  # noqa: ANN401
        """Create a Bitcaster user with the given email."""
        return self.sdk.add_user(email, first_name, last_name)

    def update_user(self, email: str, first_name: str = "", last_name: str = "") -> Any:  # noqa: ANN401
        """Update the Bitcaster user with the given email."""
        return self.sdk.update_user(email, first_name, last_name)

    def delete_user(self, email: str) -> requests.Response:
        """Delete the Bitcaster user with the given email."""
        # the sdk does not expose user deletion (yet): go through its transport
        transport = self.sdk.transport
        return transport.session.delete(transport.get_url(f"u/{urllib.parse.quote(email)}/"))
