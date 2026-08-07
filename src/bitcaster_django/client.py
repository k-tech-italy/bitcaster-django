"""Client module for interacting with Bitcaster.

Defines a `Client` facade over the bitcaster-sdk client initialized at
startup by `bitcaster_django.apps.Config.ready()` and shared across threads:
it triggers remote Bitcaster events and wraps the sdk user management API.
All Bitcaster calls made by the application should go through this class.

The underlying sdk client class is configurable via the CLIENT key of the
``BITCASTER`` settings dictionary: return values mirror the configured class
(e.g. plain data for the sync client, futures for the async one).
"""

import urllib.parse
from typing import Any

import requests
from bitcaster_sdk.abstract_client import AbstractClient
from bitcaster_sdk.client import ctx
from django.core.exceptions import ImproperlyConfigured

from bitcaster_django.config import SETTINGS_KEY, app_settings


#: process-wide sdk client shared across threads. The sdk stores its client in a
#: ContextVar, which does not propagate to threads spawned after initialization
#: (e.g. the dev server's per-request threads): this module-level reference is
#: the source of truth for the facade; `ctx` is mirrored only for code using the
#: bitcaster_sdk module-level API in the thread that ran the initialization.
_sdk_client: "AbstractClient | None" = None


def set_sdk_client(client: AbstractClient) -> None:
    """Store the shared sdk client and mirror it into the sdk ``ctx`` ContextVar."""
    global _sdk_client  # noqa: PLW0603
    _sdk_client = client
    ctx.set(client)


def get_sdk_client() -> "AbstractClient | None":
    """Return the sdk client initialized by ``Config.init_sdk()``, from any thread."""
    return _sdk_client


def _require_sdk_client() -> AbstractClient:
    client = get_sdk_client()
    if client is None or client.transport is None:
        raise ImproperlyConfigured(f"The bitcaster-sdk client is not initialized: check the {SETTINGS_KEY} setting.")
    return client


class Client:
    """
    Facade over the bitcaster-sdk client for triggering remote events and managing users.

    Relies on the sdk client initialized at startup from the ``BITCASTER``
    settings dictionary.
    """

    def __init__(self) -> None:
        _require_sdk_client()

    @property
    def sdk(self) -> AbstractClient:
        """Return the bitcaster-sdk client initialized at startup."""
        return _require_sdk_client()

    def trigger_event(self, event_name: str, context: "dict[str, str] | None" = None, **kwargs: Any) -> Any:  # noqa: ANN401
        """Trigger the remote Bitcaster event with the given name."""
        project = app_settings.project
        application = app_settings.application
        if not project:
            raise ImproperlyConfigured(f"Missing PROJECT in the {SETTINGS_KEY} setting.")
        if not application:
            raise ImproperlyConfigured(f"Missing APPLICATION in the {SETTINGS_KEY} setting.")
        # set_domain() on every call: PROJECT/APPLICATION may change at runtime via constance
        self.sdk.set_domain(project, application)
        return self.sdk.trigger_event(event_name, context=context, **kwargs)

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
