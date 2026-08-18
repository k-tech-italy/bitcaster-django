from __future__ import annotations

import typing
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.checks import run_checks
from django.test import override_settings

from bitcaster_django.advanced import AsyncClient, Client, DjangoClient, DjangoNamespace
from bitcaster_django.client import get_sdk_client


if typing.TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


pytestmark = pytest.mark.django_db

User = get_user_model()

BAE = "https://token-123@bitcaster.example.com/api/o/demo-org/"


def _user(username: str, *groups: Group) -> AbstractUser:
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username=username, email=f"{username}@example.com")
        user.groups.set(groups)
    return user


def test_django_namespace() -> None:
    assert isinstance(Client.django, DjangoNamespace)
    assert isinstance(AsyncClient.django, DjangoNamespace)
    client = Client(None)
    assert isinstance(client.django, DjangoClient)
    assert client.django.sdk_client is client


def test_trigger_for_users_invokes_trigger_event_with_filter_options() -> None:
    client = Client(None)
    with patch.object(Client, "trigger_event") as trigger_event:
        client.django.trigger_for_users("evt", ["u1", "u2"], context={"k": "v"}, options={"x": "1"}, cid="c1")
    trigger_event.assert_called_once_with(
        "evt",
        context={"k": "v"},
        options={"x": "1", "recipient_filter": {"usernames": ["u1", "u2"]}},
        cid="c1",
    )


def test_trigger_for_users_overwrites_caller_recipient_filter() -> None:
    client = Client(None)
    with patch.object(Client, "trigger_event") as trigger_event:
        client.django.trigger_for_users("evt", ["u1"], options={"recipient_filter": "junk"})
    assert trigger_event.call_args.kwargs["options"]["recipient_filter"] == {"usernames": ["u1"]}


def test_trigger_for_users_rejects_empty_list() -> None:
    with pytest.raises(ValueError, match="at least one username"):
        Client(None).django.trigger_for_users("evt", [])


def test_trigger_for_groups_resolves_group_members_once() -> None:
    g1 = Group.objects.create(name="g1")
    g2 = Group.objects.create(name="g2")
    _user("u1", g1)
    _user("u2", g1, g2)  # in both groups: must be listed exactly once
    _user("u3")  # in no group: must not be listed
    client = Client(None)
    with patch.object(Client, "trigger_event") as trigger_event:
        client.django.trigger_for_groups("evt", [g1.pk, g2.pk], context={"k": "v"})
    trigger_event.assert_called_once_with(
        "evt",
        context={"k": "v"},
        options={"recipient_filter": {"usernames": ["u1", "u2"]}},
        cid=None,
    )


def test_trigger_for_groups_without_members_rejected() -> None:
    group = Group.objects.create(name="empty")
    with pytest.raises(ValueError, match="at least one username"):
        Client(None).django.trigger_for_groups("evt", [group.pk])


def test_async_client_resolves_groups_in_calling_thread() -> None:
    # the ORM query runs before delegating to the (thread-backed) sdk call:
    # under pytest-django, touching the database from another thread would fail
    group = Group.objects.create(name="g1")
    _user("u1", group)
    client = AsyncClient(None)
    with patch.object(AsyncClient, "trigger_event") as trigger_event:
        client.django.trigger_for_groups("evt", [group.pk])
    assert trigger_event.call_args.kwargs["options"]["recipient_filter"] == {"usernames": ["u1"]}


def test_advanced_client_via_settings() -> None:
    config = {
        "BAE": BAE,
        "PROJECT": "demo-project",
        "APPLICATION": "demo-app",
        "CLIENT": "bitcaster_django.advanced.Client",
    }
    with override_settings(BITCASTER=config):
        assert run_checks(tags=["bitcaster"]) == []
        assert isinstance(get_sdk_client(), Client)
