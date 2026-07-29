from unittest.mock import patch

import pytest
from bitcaster_sdk.client import (
    Client as SdkClient,
    ctx,
)
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from bitcaster_django.client import Client
from bitcaster_django.models import EventConfig


pytestmark = pytest.mark.django_db

BAE = "https://token-123@bitcaster.example.com/api/o/demo-org/"


def test_client_requires_initialized_sdk() -> None:
    token = ctx.set(SdkClient(None))
    try:
        with pytest.raises(ImproperlyConfigured, match="not initialized"):
            Client()
    finally:
        ctx.reset(token)


def test_trigger_event() -> None:
    EventConfig.objects.create(local_name="example_local_name", remote_event_slug="example_remote_slug")
    with patch("bitcaster_sdk.client.Client.trigger") as trigger:
        Client().trigger_event("example_local_name", context={"key": "value"})
    trigger.assert_called_once_with(
        project="demo-project", application="demo-app", event="example_remote_slug", context={"key": "value"}
    )


@pytest.mark.parametrize("key", ["PROJECT", "APPLICATION"])
def test_trigger_event_without_configuration(monkeypatch, key) -> None:
    monkeypatch.delenv("BITCASTER_PROJECT_SLUG", raising=False)
    monkeypatch.delenv("BITCASTER_APPLICATION", raising=False)
    EventConfig.objects.create(local_name="example_local_name", remote_event_slug="example_remote_slug")
    config = {"BAE": BAE, "PROJECT": "demo-project", "APPLICATION": "demo-app", key: ""}
    with override_settings(BITCASTER=config):
        with pytest.raises(ImproperlyConfigured, match=f"Missing {key}"):
            Client().trigger_event("example_local_name")


def test_add_user() -> None:
    with patch("bitcaster_sdk.client.Client.add_user") as add_user:
        Client().add_user("example@mail", "John", "Doe")
    add_user.assert_called_once_with("example@mail", "John", "Doe")


def test_update_user() -> None:
    with patch("bitcaster_sdk.client.Client.update_user") as update_user:
        Client().update_user("example@mail", "Jane", "Doe")
    update_user.assert_called_once_with("example@mail", "Jane", "Doe")


def test_delete_user() -> None:
    with patch("requests.Session.delete") as session_delete:
        Client().delete_user("example@mail")
    session_delete.assert_called_once_with("https://bitcaster.example.com/api/o/demo-org/u/example%40mail/")
