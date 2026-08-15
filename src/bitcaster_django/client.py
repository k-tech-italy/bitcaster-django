"""Client module for interacting with Bitcaster.

Defines a `Client` facade over the bitcaster-sdk client initialized at
startup by `bitcaster_django.apps.Config.ready()` and shared across threads:
it maps local event names (`EventConfig`) to remote Bitcaster events and
wraps the sdk user management API. All Bitcaster calls made by the
application should go through this class.

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
from django.shortcuts import get_object_or_404

from bitcaster_django.config import SETTINGS_KEY, app_settings
from bitcaster_django.models import EventConfig


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


def _require_domain() -> "tuple[str, str]":
    """Return the configured (project, application) pair, or raise ImproperlyConfigured."""
    project = app_settings.project
    application = app_settings.application
    if not project:
        raise ImproperlyConfigured(f"Missing PROJECT in the {SETTINGS_KEY} setting.")
    if not application:
        raise ImproperlyConfigured(f"Missing APPLICATION in the {SETTINGS_KEY} setting.")
    return project, application


class Client:
    """
    Facade over the bitcaster-sdk client for triggering remote events and managing users.

    Relies on the sdk client initialized at startup from the ``BITCASTER``
    settings dictionary; uses local event configuration stored in the database
    to map local event names to remote Bitcaster event slugs.
    """

    def __init__(self) -> None:
        _require_sdk_client()

    @property
    def sdk(self) -> AbstractClient:
        """Return the bitcaster-sdk client initialized at startup."""
        return _require_sdk_client()

    def trigger_event(self, event_name: str, context: "dict[str, str] | None" = None, **kwargs: Any) -> Any:  # noqa: ANN401
        """Trigger the remote Bitcaster event mapped to the given local event name."""
        mapping = get_object_or_404(EventConfig, local_name=event_name)
        # resolved on every call: PROJECT/APPLICATION may change at runtime via constance
        project, application = _require_domain()
        self.sdk.set_domain(project, application)
        return self.sdk.trigger_event(mapping.remote_event_slug, context=context, **kwargs)

    def register_user(
        self,
        username: str,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        *,
        active: bool = True,
        custom_fields: "dict[str, Any] | None" = None,
    ) -> Any:  # noqa: ANN401
        """Register the user as member of the configured project/application.

        Creates the Bitcaster user when missing and upserts its application
        membership (including the ``active`` flag and the ``custom_fields``,
        e.g. the Django group pks used by Bitcaster filter payloads). When
        the user has an email it is passed as an address assigned to the
        preferred channels, so the resulting assignments are added to the
        distribution list configured via the DISTRIBUTION_LIST setting (if
        any).
        """
        project, application = _require_domain()
        addresses = [{"value": email, "assign_to_preferred_channel": True}] if email else []
        return self.sdk.register_user(
            project,
            application,
            username,
            first_name,
            last_name,
            email,
            custom_fields=custom_fields,
            active=active,
            addresses=addresses,
            distribution_list=app_settings.distribution_list or None,
        )

    def unregister_user(self, username: str) -> Any:  # noqa: ANN401
        """Unregister the user from the configured project/application.

        Deletes the user's application membership records; distribution list
        subscriptions are not affected.
        """
        project, application = _require_domain()
        return self.sdk.unregister_user(project, application, username)

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
