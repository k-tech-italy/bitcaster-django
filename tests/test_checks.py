import pytest
from django.core.checks import run_checks
from django.test import override_settings


BAE = "https://token@host.example.com/api/o/org/"


def _ids(messages) -> list[str]:
    return [m.id for m in messages]


def test_valid_settings() -> None:
    assert run_checks(tags=["bitcaster"]) == []


def test_missing_bae(monkeypatch) -> None:
    monkeypatch.delenv("BITCASTER_BAE", raising=False)
    with override_settings(BITCASTER={"SYNC_USERS": False}):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.E001"]


def test_invalid_bae() -> None:
    with override_settings(BITCASTER={"BAE": "https://example.com/", "SYNC_USERS": False}):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.E002"]


def test_unimportable_client() -> None:
    with override_settings(
        BITCASTER={
            "BAE": BAE,
            "SYNC_USERS": False,
            "CLIENT": "no.such.module.Client",
        }
    ):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.E003"]


def test_invalid_client_class() -> None:
    # importable, but not a bitcaster-sdk client
    with override_settings(
        BITCASTER={
            "BAE": BAE,
            "SYNC_USERS": False,
            "CLIENT": "bitcaster_django.client.Client",
        }
    ):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.E003"]


@pytest.mark.parametrize(
    ("key", "check_id"),
    [("PROJECT", "bitcaster_django.E004"), ("APPLICATION", "bitcaster_django.E005")],
)
def test_sync_users_requires_project_and_application(monkeypatch, key, check_id) -> None:
    monkeypatch.delenv("BITCASTER_PROJECT_SLUG", raising=False)
    monkeypatch.delenv("BITCASTER_APPLICATION", raising=False)
    config = {"BAE": BAE, "PROJECT": "demo-project", "APPLICATION": "demo-app", key: ""}
    with override_settings(BITCASTER=config):
        assert _ids(run_checks(tags=["bitcaster"])) == [check_id]
    with override_settings(BITCASTER={**config, "SYNC_USERS": False}):
        assert run_checks(tags=["bitcaster"]) == []


def test_unknown_key() -> None:
    with override_settings(
        BITCASTER={
            "BAE": BAE,
            "SYNC_USERS": False,
            "TIMEOUT": 10,
        }
    ):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.W001"]
