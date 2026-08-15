"""Advanced bitcaster-sdk clients with Django-aware trigger helpers.

Subclasses of the bitcaster-sdk clients exposing a ``django`` namespace with
utility methods to trigger events for a subset of the recipients (by
username or by Django group), built on top of the sdk ``trigger_event`` API
and its ``options`` parameter. Opt in by pointing the CLIENT key of the
``BITCASTER`` settings dictionary at one of these classes.
"""

from typing import TYPE_CHECKING, Any

import bitcaster_sdk.async_client
import bitcaster_sdk.client
from django.contrib.auth import get_user_model


if TYPE_CHECKING:
    from bitcaster_sdk.abstract_client import AbstractClient


class DjangoClient:
    """Django utility namespace bound to a bitcaster-sdk client.

    Keeps the Django-specific behaviour out of the sdk classes: the methods
    build a recipient filter and delegate to the wrapped client's
    ``trigger_event``, so the domain must have been set (``set_domain``)
    exactly as for a plain ``trigger_event`` call, and return values mirror
    the wrapped client (plain data for the sync client, futures for the
    async one).
    """

    def __init__(self, sdk_client: "AbstractClient") -> None:
        """Bind the namespace to the sdk client it extends."""
        self.sdk_client = sdk_client

    def trigger_for_users(
        self,
        event: str,
        usernames: "list[str]",
        context: "dict[str, str] | None" = None,
        options: "dict[str, Any] | None" = None,
        cid: "str | None" = None,
    ) -> Any:  # noqa: ANN401
        """Trigger the event only for the users identified by their username.

        The recipient filter is carried by the ``options`` parameter of the
        sdk ``trigger_event`` API; caller-provided options are preserved,
        except for the ``recipient_filter`` key which is overwritten.

        Raises ValueError on an empty username list: silently sending an
        empty filter could target every recipient instead of none.
        """
        if not usernames:
            raise ValueError("trigger_for_users() requires at least one username")
        options = {**(options or {}), "recipient_filter": {"usernames": list(usernames)}}
        return self.sdk_client.trigger_event(event, context=context, options=options, cid=cid)

    def trigger_for_groups(
        self,
        event: str,
        groups: "list[int]",
        context: "dict[str, str] | None" = None,
        options: "dict[str, Any] | None" = None,
        cid: "str | None" = None,
    ) -> Any:  # noqa: ANN401
        """Trigger the event only for the users belonging to at least one of the given Django groups.

        The group pks are resolved to usernames with the local Django
        database (the source of truth for the memberships synced with
        Bitcaster); the query runs in the calling thread even with the
        async client. Raises ValueError when no user belongs to the groups.
        """
        user_model = get_user_model()
        usernames = list(
            user_model.objects.filter(groups__pk__in=groups)
            .distinct()
            .order_by(user_model.USERNAME_FIELD)
            .values_list(user_model.USERNAME_FIELD, flat=True)
        )
        return self.trigger_for_users(event, usernames, context=context, options=options, cid=cid)


class DjangoNamespace:
    """Descriptor returning the Django utility namespace bound to the sdk client instance."""

    def __get__(self, obj: "AbstractClient | None", objtype: "type | None" = None) -> "DjangoClient | DjangoNamespace":
        """Return the bound ``DjangoClient`` (or the descriptor itself on class access)."""
        if obj is None:
            return self
        return DjangoClient(obj)


class Client(bitcaster_sdk.client.Client):
    """bitcaster-sdk sync client extended with the ``django`` utility namespace."""

    django = DjangoNamespace()


class AsyncClient(bitcaster_sdk.async_client.AsyncClient):
    """bitcaster-sdk async client extended with the ``django`` utility namespace."""

    django = DjangoNamespace()
