"""bitcaster-django specific signal handlers."""

import logging
from typing import TYPE_CHECKING

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signals import request_started
from django.db.models.signals import m2m_changed, post_delete, post_save
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


def _group_pks(instance: "Model") -> list[int]:
    """Return the pks of the groups the user is assigned to (empty when the model has no groups)."""
    groups = getattr(instance, "groups", None)
    if groups is None:
        return []
    return sorted(groups.values_list("pk", flat=True))


def _register(instance: "Model") -> None:
    """Register the Django user with Bitcaster, without ever raising."""
    username = instance.get_username()
    try:
        Client().register_user(
            username,
            getattr(instance, "first_name", "") or "",
            getattr(instance, "last_name", "") or "",
            getattr(instance, "email", "") or "",
            active=bool(getattr(instance, "is_active", True)),
            custom_fields={"groups": _group_pks(instance)},
        )
    except Exception:  # syncing must never break the saving of a Django user
        logger.exception("unable to register user '%s' with Bitcaster", username)


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid="bitcaster_django.sync_user")
def sync_user(sender: "type[Model]", instance: "Model", created: bool, raw: bool = False, **kwargs: object) -> None:
    """Keep the matching Bitcaster application membership aligned with the Django user.

    Registration is idempotent: the Bitcaster user is created when missing
    and its membership is upserted, so creation, update and (de)activation
    are all handled by the same call. ``is_active`` maps to the membership
    ``active`` flag; models without the attribute are treated as active.
    The membership custom fields carry the pks of the groups the user is
    assigned to (``{"groups": [...]}``), so Bitcaster filter payloads can
    target only the users belonging to a given Django group.
    """
    if raw or not app_settings.SYNC_USERS:
        return
    _register(instance)


def sync_user_groups(
    sender: "type[Model]", instance: "Model", action: str, reverse: bool, pk_set: "set[int] | None", **kwargs: object
) -> None:
    """Re-register the affected users when their group assignments change.

    Group assignments go through the m2m relation and do not emit
    ``post_save``. On the reverse relation (``group.user_set``) each user in
    ``pk_set`` is re-registered; a reverse ``.clear()`` provides no pk set,
    so the affected users cannot be synced (documented limitation).
    """
    if action not in ("post_add", "post_remove", "post_clear") or not app_settings.SYNC_USERS:
        return
    if reverse:
        for user in get_user_model().objects.filter(pk__in=pk_set or ()):
            _register(user)
    else:
        _register(instance)


# the through model only exists on user models with a `groups` relation
if hasattr(get_user_model(), "groups"):
    m2m_changed.connect(
        sync_user_groups,
        sender=get_user_model().groups.through,
        dispatch_uid="bitcaster_django.sync_user_groups",
    )


@receiver(post_delete, sender=settings.AUTH_USER_MODEL, dispatch_uid="bitcaster_django.unregister_user")
def unregister_user(sender: "type[Model]", instance: "Model", **kwargs: object) -> None:
    """Unregister the matching Bitcaster user when the Django one is deleted.

    Unregistering a user unknown to Bitcaster is not an error: failures are
    logged (with the username, to allow manual reconciliation) and swallowed.
    """
    if not app_settings.SYNC_USERS:
        return
    username = instance.get_username()
    try:
        Client().unregister_user(username)
    except Exception:  # syncing must never break the deletion of a Django user
        logger.exception("unable to unregister user '%s' from Bitcaster", username)


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
