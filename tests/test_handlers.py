import logging
from unittest.mock import patch

import pytest
from bitcaster_sdk.exceptions import EventNotFoundError
from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import override_settings


pytestmark = pytest.mark.django_db

User = get_user_model()


def test_user_creation_adds_bitcaster_user() -> None:
    with patch("bitcaster_sdk.client.Client.add_user") as add_user:
        User.objects.create(username="u1", email="u1@example.com", first_name="John", last_name="Doe")
    add_user.assert_called_once_with("u1@example.com", "John", "Doe")


def test_user_update_updates_bitcaster_user() -> None:
    with patch("bitcaster_sdk.client.Client.add_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with patch("bitcaster_sdk.client.Client.update_user") as update_user:
        user.first_name = "Jane"
        user.save()
    update_user.assert_called_once_with("u1@example.com", "Jane", "")


def test_user_update_falls_back_to_add() -> None:
    with patch("bitcaster_sdk.client.Client.add_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with (
        patch("bitcaster_sdk.client.Client.update_user", side_effect=EventNotFoundError) as update_user,
        patch("bitcaster_sdk.client.Client.add_user") as add_user,
    ):
        user.save()
    update_user.assert_called_once()
    add_user.assert_called_once_with("u1@example.com", "", "")


def test_user_without_email_is_ignored() -> None:
    with patch("bitcaster_sdk.client.Client.add_user") as add_user:
        User.objects.create(username="u1")
    add_user.assert_not_called()


def test_sync_disabled() -> None:
    with override_settings(BITCASTER={"BAE": "https://token@host.example.com/api/o/org/", "SYNC_USERS": False}):
        with patch("bitcaster_sdk.client.Client.add_user") as add_user:
            User.objects.create(username="u1", email="u1@example.com")
    add_user.assert_not_called()


def test_sdk_errors_do_not_break_save(caplog) -> None:
    caplog.set_level(logging.ERROR, logger="bitcaster_django.handlers")
    with patch("bitcaster_sdk.client.Client.add_user", side_effect=ConnectionError("boom")):
        user = User.objects.create(username="u1", email="u1@example.com")
    assert user.pk is not None
    assert "unable to sync user 'u1@example.com'" in caplog.text


def test_unrelated_setting_change_does_not_reinitialize() -> None:
    app_config = apps.get_app_config("bitcaster_django")
    with patch.object(app_config, "init_sdk") as init_sdk:
        with override_settings(LANGUAGE_CODE="it"):
            pass
    init_sdk.assert_not_called()
