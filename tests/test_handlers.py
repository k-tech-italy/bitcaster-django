import logging
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import override_settings


pytestmark = pytest.mark.django_db

User = get_user_model()

BAE = "https://token@host.example.com/api/o/org/"
SYNC_OFF = {"BAE": BAE, "SYNC_USERS": False}


def test_user_creation_registers_bitcaster_user() -> None:
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        User.objects.create(username="u1", email="u1@example.com", first_name="John", last_name="Doe")
    register_user.assert_called_once_with(
        "u1", "John", "Doe", "u1@example.com", active=True, custom_fields={"groups": []}
    )


def test_user_update_registers_bitcaster_user() -> None:
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        user.first_name = "Jane"
        user.save()
    register_user.assert_called_once_with("u1", "Jane", "", "u1@example.com", active=True, custom_fields={"groups": []})


def test_user_deactivation_registers_inactive_membership() -> None:
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        user.is_active = False
        user.save()
    register_user.assert_called_once_with("u1", "", "", "u1@example.com", active=False, custom_fields={"groups": []})


def test_user_reactivation_registers_active_membership() -> None:
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com", is_active=False)
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        user.is_active = True
        user.save()
    register_user.assert_called_once_with("u1", "", "", "u1@example.com", active=True, custom_fields={"groups": []})


def test_user_without_email_is_registered() -> None:
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        User.objects.create(username="u1")
    register_user.assert_called_once_with("u1", "", "", "", active=True, custom_fields={"groups": []})


def test_group_assignment_reregisters_user() -> None:
    group = Group.objects.create(name="g1")
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        user.groups.add(group)
    register_user.assert_called_once_with(
        "u1", "", "", "u1@example.com", active=True, custom_fields={"groups": [group.pk]}
    )
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        user.groups.remove(group)
    register_user.assert_called_once_with("u1", "", "", "u1@example.com", active=True, custom_fields={"groups": []})


def test_reverse_group_assignment_reregisters_users() -> None:
    group = Group.objects.create(name="g1")
    with patch("bitcaster_django.client.Client.register_user"):
        u1 = User.objects.create(username="u1", email="u1@example.com")
        u2 = User.objects.create(username="u2", email="u2@example.com")
    with patch("bitcaster_django.client.Client.register_user") as register_user:
        group.user_set.add(u1, u2)
    assert register_user.call_count == 2
    assert {call.args[0] for call in register_user.call_args_list} == {"u1", "u2"}


def test_group_sync_disabled() -> None:
    group = Group.objects.create(name="g1")
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with override_settings(BITCASTER=SYNC_OFF):
        with patch("bitcaster_django.client.Client.register_user") as register_user:
            user.groups.add(group)
    register_user.assert_not_called()


def test_user_deletion_unregisters_bitcaster_user() -> None:
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with patch("bitcaster_django.client.Client.unregister_user") as unregister_user:
        user.delete()
    unregister_user.assert_called_once_with("u1")


def test_sync_disabled() -> None:
    with override_settings(BITCASTER=SYNC_OFF):
        with patch("bitcaster_django.client.Client.register_user") as register_user:
            user = User.objects.create(username="u1", email="u1@example.com")
        with patch("bitcaster_django.client.Client.unregister_user") as unregister_user:
            user.delete()
    register_user.assert_not_called()
    unregister_user.assert_not_called()


def test_sdk_errors_do_not_break_save(caplog) -> None:
    caplog.set_level(logging.ERROR, logger="bitcaster_django.handlers")
    with patch("bitcaster_django.client.Client.register_user", side_effect=ConnectionError("boom")):
        user = User.objects.create(username="u1", email="u1@example.com")
    assert user.pk is not None
    assert "unable to register user 'u1' with Bitcaster" in caplog.text


def test_sdk_errors_do_not_break_delete(caplog) -> None:
    caplog.set_level(logging.ERROR, logger="bitcaster_django.handlers")
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with patch("bitcaster_django.client.Client.unregister_user", side_effect=ConnectionError("boom")):
        user.delete()
    assert not User.objects.filter(username="u1").exists()
    assert "unable to unregister user 'u1' from Bitcaster" in caplog.text


def test_unregistering_unknown_user_does_not_raise() -> None:
    with patch("bitcaster_django.client.Client.register_user"):
        user = User.objects.create(username="u1", email="u1@example.com")
    with patch("bitcaster_django.client.Client.unregister_user", side_effect=Exception("404 Not Found")):
        user.delete()
    assert not User.objects.filter(username="u1").exists()
