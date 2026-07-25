"""bitcaster-django specific signal handlers."""

import logging
from typing import TYPE_CHECKING

from bitcaster_sdk.exceptions import EventNotFoundError
from django.apps import apps
from django.conf import settings
from django.core.signals import request_started
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.test.signals import setting_changed

from .client import Client
from .config import SETTINGS_KEY, app_settings

try:
    from constance.signals import config_updated
except ImportError:  # constance is an optional dependency
    config_updated = None

if TYPE_CHECKING:
    from django.db.models import Model

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid="bitcaster_django.sync_user")
def sync_user(sender: "type[Model]", instance: "Model", created: bool, raw: bool = False, **kwargs: object) -> None:
    """Keep the matching Bitcaster user aligned with the Django one."""
    if raw or not app_settings.SYNC_USERS:
        return
    email = getattr(instance, "email", "") or ""
    if not email:
        return
    first_name = getattr(instance, "first_name", "") or ""
    last_name = getattr(instance, "last_name", "") or ""
    try:
        bitcaster = Client()
        if created:
            bitcaster.add_user(email, first_name, last_name)
        else:
            try:
                bitcaster.update_user(email, first_name, last_name)
            except EventNotFoundError:
                # the user predates the Bitcaster integration
                bitcaster.add_user(email, first_name, last_name)
    except Exception:  # syncing must never break the saving of a Django user
        logger.exception("unable to sync user '%s' with Bitcaster", email)


@receiver(setting_changed, dispatch_uid="bitcaster_django.setting_changed")
def on_setting_changed(sender: object, setting: str, **kwargs: object) -> None:
    """Reinitialize the sdk client when ``BITCASTER`` is overridden (e.g. in tests)."""
    if setting == SETTINGS_KEY:
        apps.get_app_config("bitcaster_django").init_sdk()


if config_updated is not None:

    @receiver(config_updated, dispatch_uid="bitcaster_django.config_updated")
    def on_config_updated(sender: object, key: str, **kwargs: object) -> None:
        """Reinitialize the sdk client when a ``BITCASTER_*`` constance key is updated."""
        if key.startswith(f"{SETTINGS_KEY}_"):
            apps.get_app_config("bitcaster_django").init_sdk()

    @receiver(request_started, dispatch_uid="bitcaster_django.first_request")
    def on_first_request(sender: object, **kwargs: object) -> None:
        """Reinitialize the sdk client once the constance backend is reachable.

        At startup the client is initialized from the static settings only (the
        constance backend cannot be queried yet): the first request picks up any
        ``BITCASTER_*`` value stored in constance.
        """
        request_started.disconnect(dispatch_uid="bitcaster_django.first_request")
        apps.get_app_config("bitcaster_django").init_sdk()
