"""Regression tests for issue #8: the sdk client must be visible from worker threads.

The sdk stores its client in a ContextVar, which does not propagate to threads
spawned after initialization (e.g. the dev server's per-request threads); the
facade must rely on process-wide state instead. Tests use real ``threading.Thread``
objects on purpose: ``ThreadPoolExecutor``/``sync_to_async`` copy or propagate
the context and would pass spuriously.
"""

import threading
from typing import Any, Callable
from unittest.mock import patch

import pytest
from bitcaster_sdk.client import Client as SdkClient
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from bitcaster_django.client import Client


def run_in_thread(fn: Callable[[], Any]) -> dict[str, Any]:
    """Run ``fn`` in a fresh thread, returning ``{"value": ...}`` or ``{"error": exc}``."""
    result: dict[str, Any] = {}

    def target() -> None:
        try:
            result["value"] = fn()
        except Exception as e:  # noqa: BLE001
            result["error"] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    return result


def test_client_works_in_fresh_thread() -> None:
    apps.get_app_config("bitcaster_django").init_sdk()
    result = run_in_thread(lambda: Client().sdk.base_url)
    assert "error" not in result, result["error"]
    assert result["value"] == "https://bitcaster.example.com/api/o/demo-org/"


def test_add_user_in_fresh_thread() -> None:
    apps.get_app_config("bitcaster_django").init_sdk()
    with patch("bitcaster_sdk.client.Client.add_user") as add_user:
        result = run_in_thread(lambda: Client().add_user("u@example.com"))
    assert "error" not in result, result["error"]
    add_user.assert_called_once_with("u@example.com", "", "")


@pytest.mark.parametrize("holder", [SdkClient(None), None], ids=["sentinel", "never-initialized"])
def test_unconfigured_client_raises_improperly_configured_in_fresh_thread(holder: "SdkClient | None") -> None:
    with patch("bitcaster_django.client._sdk_client", holder):
        result = run_in_thread(Client)
    assert isinstance(result.get("error"), ImproperlyConfigured)


def test_reinit_in_one_thread_visible_to_others() -> None:
    other_bae = "https://tok@other.example.com/api/o/other-org/"
    with override_settings(BITCASTER={"BAE": other_bae}):
        # simulate the constance-driven re-init done by the first-request worker thread
        init_sdk = apps.get_app_config("bitcaster_django").init_sdk
        assert "error" not in run_in_thread(init_sdk)
        result = run_in_thread(lambda: Client().sdk.base_url)
        assert "error" not in result, result["error"]
        assert result["value"] == "https://other.example.com/api/o/other-org/"
        assert Client().sdk.base_url == "https://other.example.com/api/o/other-org/"
    # leaving override_settings fires setting_changed, restoring the demo client
    assert Client().sdk.base_url == "https://bitcaster.example.com/api/o/demo-org/"
