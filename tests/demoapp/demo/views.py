"""Demo views showcasing the bitcaster-django features.

Every endpoint is a browsable GET view returning JSON, so the whole feature
set can be exercised from a browser (or curl) without writing any code:

* the user lifecycle endpoints demonstrate the automatic Bitcaster
  register/unregister performed by the ``bitcaster_django.handlers`` signal
  receivers (creation, update, deactivation, deletion, group changes);
* the trigger endpoints demonstrate the ``Client`` facade (local event names
  mapped by ``EventConfig``) and the advanced client's ``django`` namespace
  (``trigger_for_users`` / ``trigger_for_groups``).
"""

import functools
from typing import Any, Callable

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from bitcaster_django.client import Client
from bitcaster_django.config import app_settings
from bitcaster_django.models import EventConfig


User = get_user_model()


def _json(payload: Any, status: int = 200) -> JsonResponse:  # noqa: ANN401
    return JsonResponse(payload, status=status, safe=False, json_dumps_params={"indent": 2})


def _user_payload(user: Any) -> dict[str, Any]:  # noqa: ANN401
    return {
        "username": user.get_username(),
        "email": user.email,
        "is_active": user.is_active,
        "groups": {group.pk: group.name for group in user.groups.all()},
    }


def bitcaster_errors(view: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    """Turn Bitcaster/configuration errors into a readable JSON response."""

    @functools.wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            return view(request, *args, **kwargs)
        except Exception as e:  # noqa: BLE001  # demo tool: show the failure, don't 500
            return _json({"error": f"{type(e).__name__}: {e}"}, status=502)

    return wrapper


def index(request: HttpRequest) -> HttpResponse:
    """Landing page listing the demo endpoints and the current configuration."""
    endpoints = {
        "user lifecycle (auto register/unregister in Bitcaster)": {
            "list users": "/users/",
            "create (registers)": "/users/add/<username>/?first_name=&last_name=",
            "update (re-registers)": "/users/<username>/update/?first_name=&last_name=",
            "deactivate (inactive membership)": "/users/<username>/deactivate/",
            "activate (active membership)": "/users/<username>/activate/",
            "delete (unregisters)": "/users/<username>/delete/",
            "add to group (custom_fields.groups)": "/users/<username>/groups/<group>/add/",
            "remove from group": "/users/<username>/groups/<group>/remove/",
        },
        "event triggering": {
            "facade, local name via EventConfig": "/trigger/<event>/?key=value",
            "advanced client, only given usernames": "/trigger/<event>/users/?u=<username>&u=...",
            "advanced client, only given group pks/names": "/trigger/<event>/groups/?g=<group>&g=...",
        },
        "admin (users, groups, EventConfig, constance runtime config)": "/admin/",
    }
    config = {
        "BAE": app_settings.bae,
        "PROJECT": app_settings.project,
        "APPLICATION": app_settings.application,
        "DISTRIBUTION_LIST": app_settings.distribution_list,
        "SYNC_USERS": app_settings.SYNC_USERS,
        "CLIENT": app_settings.CLIENT,
    }
    return _json({"bitcaster-django demo": endpoints, "current configuration": config})


def users(request: HttpRequest) -> HttpResponse:
    """List the demo users and their group assignments."""
    return _json([_user_payload(user) for user in User.objects.order_by("username")])


@bitcaster_errors
def user_add(request: HttpRequest, username: str) -> HttpResponse:
    """Create a user: the post_save handler registers it with Bitcaster."""
    user = User.objects.create(
        username=username,
        email=request.GET.get("email", f"{username}@example.com"),
        first_name=request.GET.get("first_name", ""),
        last_name=request.GET.get("last_name", ""),
    )
    return _json({"created (and registered with Bitcaster)": _user_payload(user)})


@bitcaster_errors
def user_update(request: HttpRequest, username: str) -> HttpResponse:
    """Update a user's names: the post_save handler re-registers it."""
    user = get_object_or_404(User, username=username)
    user.first_name = request.GET.get("first_name", user.first_name)
    user.last_name = request.GET.get("last_name", user.last_name)
    user.save()
    return _json({"updated (and re-registered with Bitcaster)": _user_payload(user)})


@bitcaster_errors
def user_set_active(request: HttpRequest, username: str, active: bool) -> HttpResponse:
    """(De)activate a user: the membership `active` flag mirrors `is_active`."""
    user = get_object_or_404(User, username=username)
    user.is_active = active
    user.save()
    return _json({f"membership marked {'active' if active else 'inactive'} in Bitcaster": _user_payload(user)})


@bitcaster_errors
def user_delete(request: HttpRequest, username: str) -> HttpResponse:
    """Delete a user: the post_delete handler unregisters it from Bitcaster."""
    user = get_object_or_404(User, username=username)
    payload = _user_payload(user)
    user.delete()
    return _json({"deleted (and unregistered from Bitcaster)": payload})


@bitcaster_errors
def user_group(request: HttpRequest, username: str, group: str, add: bool) -> HttpResponse:
    """(Un)assign a group: the m2m_changed handler updates custom_fields['groups']."""
    user = get_object_or_404(User, username=username)
    group_obj, _ = Group.objects.get_or_create(name=group)
    if add:
        user.groups.add(group_obj)
    else:
        user.groups.remove(group_obj)
    return _json({"groups synced to Bitcaster custom_fields": _user_payload(user)})


def _remote_slug(event: str) -> str:
    """Resolve a local event name via EventConfig, falling back to the name itself."""
    mapping = EventConfig.objects.filter(local_name=event).first()
    return mapping.remote_event_slug if mapping else event


def _advanced_sdk() -> Any:  # noqa: ANN401
    """Return the configured sdk client, ensuring it exposes the `django` namespace."""
    sdk = Client().sdk
    if not hasattr(sdk, "django"):
        raise TypeError(
            f"the configured client ({type(sdk).__module__}.{type(sdk).__qualname__}) is not an advanced "
            f'client: set BITCASTER = {{"CLIENT": "bitcaster_django.advanced.Client"}} (or AsyncClient)'
        )
    sdk.set_domain(app_settings.project, app_settings.application)
    return sdk


def _resolved(result: Any) -> Any:  # noqa: ANN401
    """Resolve async client futures so the response is always plain data."""
    return result.result() if hasattr(result, "result") else result


@bitcaster_errors
def trigger(request: HttpRequest, event: str) -> HttpResponse:
    """Trigger an event by its local name through the Client facade."""
    result = Client().trigger_event(event, context=dict(request.GET.items()))
    return _json({"triggered": event, "response": _resolved(result)})


@bitcaster_errors
def trigger_users(request: HttpRequest, event: str) -> HttpResponse:
    """Trigger an event only for the usernames in the `u` query parameters."""
    usernames = request.GET.getlist("u")
    result = _advanced_sdk().django.trigger_for_users(_remote_slug(event), usernames)
    return _json({"triggered": event, "for users": usernames, "response": _resolved(result)})


@bitcaster_errors
def trigger_groups(request: HttpRequest, event: str) -> HttpResponse:
    """Trigger an event only for the members of the groups in the `g` query parameters (pks or names)."""
    groups = [
        group.pk
        for g in request.GET.getlist("g")
        for group in [get_object_or_404(Group, pk=g) if g.isdigit() else get_object_or_404(Group, name=g)]
    ]
    result = _advanced_sdk().django.trigger_for_groups(_remote_slug(event), groups)
    return _json({"triggered": event, "for groups": groups, "response": _resolved(result)})
