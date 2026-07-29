from django.core.checks import run_checks
from django.test import override_settings


def _ids(messages) -> list[str]:
    return [m.id for m in messages]


def test_valid_settings() -> None:
    assert run_checks(tags=["bitcaster"]) == []


def test_missing_bae(monkeypatch) -> None:
    monkeypatch.delenv("BITCASTER_BAE", raising=False)
    with override_settings(BITCASTER={}):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.E001"]


def test_invalid_bae() -> None:
    with override_settings(BITCASTER={"BAE": "https://example.com/"}):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.E002"]


def test_unknown_key() -> None:
    with override_settings(
        BITCASTER={
            "BAE": "https://token@host.example.com/api/o/org/",
            "TIMEOUT": 10,
        }
    ):
        assert _ids(run_checks(tags=["bitcaster"])) == ["bitcaster_django.W001"]
