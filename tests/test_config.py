import pytest
from bitcaster_sdk import client
from bitcaster_sdk.async_client import AsyncClient
from bitcaster_sdk.client import Client
from django.test import override_settings

from bitcaster_django.config import app_settings


def test_defaults() -> None:
    with override_settings(BITCASTER={}):
        assert app_settings.BAE == ""
        assert app_settings.DEBUG is False
        assert app_settings.SYNC_USERS is True


def test_bae_from_settings() -> None:
    assert app_settings.bae == "https://token-123@bitcaster.example.com/api/o/demo-org/"


def test_bae_env_fallback(monkeypatch) -> None:
    monkeypatch.setenv("BITCASTER_BAE", "https://key@host.example.com/api/o/org/")
    with override_settings(BITCASTER={}):
        assert app_settings.bae == "https://key@host.example.com/api/o/org/"


def test_project_application_env_fallback(monkeypatch) -> None:
    monkeypatch.setenv("BITCASTER_PROJECT_SLUG", "env-project")
    monkeypatch.setenv("BITCASTER_APPLICATION", "env-app")
    with override_settings(BITCASTER={}):
        assert app_settings.project == "env-project"
        assert app_settings.application == "env-app"


def test_sdk_options_forwards_lowercased() -> None:
    with override_settings(
        BITCASTER={"BAE": "x", "DEBUG": True, "SYNC_USERS": False, "CLIENT": "bitcaster_sdk.client.Client"}
    ):
        assert app_settings.sdk_options() == {"debug": True}


def test_client_class_default() -> None:
    with override_settings(BITCASTER={}):
        assert app_settings.client_class is Client


def test_client_class_invalid() -> None:
    with override_settings(BITCASTER={"CLIENT": "no.such.module.Client"}):
        with pytest.raises(ImportError):
            _ = app_settings.client_class


def test_client_initialized_on_startup() -> None:
    bitcaster = client.ctx.get()
    assert bitcaster.transport is not None
    assert bitcaster.base_url == "https://bitcaster.example.com/api/o/demo-org/"


def test_client_reinitialized_on_override_settings() -> None:
    with override_settings(BITCASTER={"BAE": "https://other-token@other.example.com/api/o/other-org/"}):
        assert client.ctx.get().base_url == "https://other.example.com/api/o/other-org/"
    assert client.ctx.get().base_url == "https://bitcaster.example.com/api/o/demo-org/"


def test_async_client_from_settings() -> None:
    with override_settings(
        BITCASTER={
            "BAE": "https://token-123@bitcaster.example.com/api/o/demo-org/",
            "CLIENT": "bitcaster_sdk.async_client.AsyncClient",
        }
    ):
        bitcaster = client.ctx.get()
        assert isinstance(bitcaster, AsyncClient)
        assert bitcaster.transport is not None
        bitcaster.close()
    assert isinstance(client.ctx.get(), Client)
