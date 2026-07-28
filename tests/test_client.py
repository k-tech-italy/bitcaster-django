from unittest.mock import patch

import pytest

from bitcaster_django.client import Client
from bitcaster_django.models import EventConfig


def test_create_client_without_bitcaster_bae_variable(monkeypatch):
    monkeypatch.delenv("BITCASTER_BAE", False)
    with pytest.raises(RuntimeError, match="Missing required environment variable BITCASTER_BAE"):
        Client()


@pytest.mark.parametrize(
    "bitcaster_bae",
    [
        "some_random_string",
        "dummytoken@dummyhost/api/o/dummyorg",
        "https://dummytoken@dummyhost/dummyorg",
        "https://dummytoken@dummyhost/api/o/",
        "https://dummyhost/api/o/dummyorg",
        12345,
        "https:/dummytoken@dummyhost/api/o/dummyorg",
    ],
)
def test_create_client_with_incorrect_bitcaster_bae_variable(monkeypatch, bitcaster_bae):
    monkeypatch.setenv("BITCASTER_BAE", bitcaster_bae)
    with pytest.raises(RuntimeError, match="Invalid BITCASTER_BAE format"):
        Client()


@pytest.mark.django_db
def test_trigger_event(monkeypatch):
    with patch("bitcaster_sdk.trigger") as mock_trigger:
        monkeypatch.setenv("BITCASTER_PROJECT_SLUG", "example_project")
        monkeypatch.setenv("BITCASTER_APPLICATION", "example_application")

        import bitcaster_sdk

        bitcaster_sdk.init()
        client = Client()

        obj = EventConfig.objects.create(local_name="example_local_name", remote_event_slug="example_remote_slug")
        assert str(obj) == "example_local_name"

        client.trigger_event("example_local_name")

        mock_trigger.assert_called_once_with(
            project="example_project", application="example_application", event="example_remote_slug"
        )


@pytest.mark.parametrize("env_variable", [("BITCASTER_PROJECT_SLUG"), ("BITCASTER_APPLICATION")])
@pytest.mark.django_db
def test_trigger_event_without_env_variables(monkeypatch, env_variable):
    with patch("bitcaster_sdk.trigger"):
        monkeypatch.setenv("BITCASTER_PROJECT_SLUG", "example_project")
        monkeypatch.setenv("BITCASTER_APPLICATION", "example_application")
        monkeypatch.delenv(env_variable, False)

        import bitcaster_sdk

        bitcaster_sdk.init()
        client = Client()

        EventConfig.objects.create(local_name="example_local_name", remote_event_slug="example_remote_slug")

        with pytest.raises(RuntimeError, match=f"Missing required environment variable {env_variable}"):
            client.trigger_event("example_local_name")


@pytest.mark.parametrize("method", [("post"), ("delete"), ("put"), ("get")])
def test_client_request(monkeypatch, method):
    client = Client()
    url = "/example_url/"
    data = {"example_key_1": "example_data_1", "example_key_2": "example_data_2"}
    method_map = {"post": client.post, "delete": client.delete, "put": client.put, "get": client.get}
    with patch("requests.request") as mock_request:
        method_map[method](url, data=data)

        mock_request.assert_called_once()
        mock_request.assert_called_with(
            method,
            "https://dummyhost/api/o/dummyorg/example_url/",
            headers={"Authorization": "Key dummytoken"},
            timeout=15,
            data={"example_key_1": "example_data_1", "example_key_2": "example_data_2"},
        )
