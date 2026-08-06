from unittest.mock import patch

import pytest
from bitcaster_sdk.client import Client as SdkClient
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from bitcaster_django.client import Client
from bitcaster_django.models import EventConfig


pytestmark = pytest.mark.django_db

BAE = "https://token-123@bitcaster.example.com/api/o/demo-org/"


def test_client_requires_initialized_sdk() -> None:
    with patch("bitcaster_django.client._sdk_client", SdkClient(None)):
        with pytest.raises(ImproperlyConfigured, match="not initialized"):
            Client()


def test_trigger_event() -> None:
    EventConfig.objects.create(local_name="example_local_name", remote_event_slug="example_remote_slug")
    with (
        patch("bitcaster_sdk.client.Client.set_domain") as set_domain,
        patch("bitcaster_sdk.client.Client.trigger_event") as trigger_event,
    ):
        Client().trigger_event("example_local_name", context={"key": "value"})
    set_domain.assert_called_once_with("demo-project", "demo-app")
    trigger_event.assert_called_once_with("example_remote_slug", context={"key": "value"})


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
