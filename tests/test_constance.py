from unittest.mock import patch

import pytest
from bitcaster_sdk import client
from constance import config
from constance.signals import config_updated
from django.apps import apps
from django.core.signals import request_started

from bitcaster_django.config import app_settings


pytestmark = pytest.mark.django_db

CONSTANCE_BAE = "https://tok-999@constance.example.com/api/o/runtime-org/"


def test_constance_value_overrides_settings() -> None:
    config.BITCASTER_BAE = CONSTANCE_BAE
    try:
        assert app_settings.bae == CONSTANCE_BAE
    finally:
        config.BITCASTER_BAE = ""


def test_empty_constance_value_falls_back_to_settings() -> None:
    assert config.BITCASTER_BAE == ""
    assert app_settings.bae == "https://token-123@bitcaster.example.com/api/o/demo-org/"


def test_config_updated_reinitializes_client() -> None:
    config.BITCASTER_BAE = CONSTANCE_BAE
    try:
        assert client.ctx.get().base_url == "https://constance.example.com/api/o/runtime-org/"
    finally:
        config.BITCASTER_BAE = ""
    assert client.ctx.get().base_url == "https://bitcaster.example.com/api/o/demo-org/"


def test_unrelated_constance_key_does_not_reinitialize() -> None:
    app_config = apps.get_app_config("bitcaster_django")
    with patch.object(app_config, "init_sdk") as init_sdk:
        config_updated.send(sender=None, key="OTHER", old_value="", new_value="x")
    init_sdk.assert_not_called()


def test_first_request_reinitializes_client_once() -> None:
    app_config = apps.get_app_config("bitcaster_django")
    with patch.object(app_config, "init_sdk") as init_sdk:
        request_started.send(sender=None)
    init_sdk.assert_called_once()
    with patch.object(app_config, "init_sdk") as init_sdk:
        request_started.send(sender=None)
    init_sdk.assert_not_called()
