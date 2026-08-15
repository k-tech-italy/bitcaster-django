---
title: Getting started
---

# How to use bitcaster-django

## Configuration

Add `bitcaster_django` to `INSTALLED_APPS` and configure the app with the
`BITCASTER` dictionary in your settings:

```python
INSTALLED_APPS = [
    ...
    "bitcaster_django",
]

BITCASTER = {
    # Bitcaster Application Endpoint.
    # Falls back to the BITCASTER_BAE environment variable when empty/omitted.
    "BAE": "https://<token>@<host>/api/o/<organization>/",
    # forwarded to the sdk client (optional, default: False)
    "DEBUG": False,
    # keep Bitcaster users aligned with Django users (optional, default: True)
    "SYNC_USERS": True,
    # project/application slugs used by Client.trigger_event() and the user
    # synchronisation (required when SYNC_USERS is enabled).
    # Fall back to the BITCASTER_PROJECT_SLUG / BITCASTER_APPLICATION
    # environment variables when empty/omitted.
    "PROJECT": "myprj",
    "APPLICATION": "myapp",
    # distribution list synced users are subscribed to (optional).
    # Falls back to the BITCASTER_DISTRIBUTION_LIST environment variable.
    "DISTRIBUTION_LIST": "mylist",
    # fully qualified name of the sdk client class to use
    # (optional, default: "bitcaster_sdk.client.Client")
    "CLIENT": "bitcaster_sdk.async_client.AsyncClient",
}
```

All keys except `BAE`, `SYNC_USERS`, `PROJECT`, `APPLICATION`,
`DISTRIBUTION_LIST` and `CLIENT` are forwarded (lowercased) to the
[bitcaster-sdk](https://github.com/bitcaster-io/bitcaster-sdk) client
constructor, so any bitcaster-sdk option can be configured from the dictionary.

`CLIENT` selects the sdk client implementation: the default
`bitcaster_sdk.client.Client` blocks on every call, while
`bitcaster_sdk.async_client.AsyncClient` runs requests on a background thread
and returns `concurrent.futures.Future` objects. Any other fully qualified
name of a `bitcaster_sdk.abstract_client.AbstractClient` subclass works too.

The configuration is validated by the Django system check framework:

```bash
python manage.py check
```

## Usage

### Triggering events

Map a local event name to a remote Bitcaster event slug with the `EventConfig`
model (e.g. from the Django admin or a data migration):

```python
from bitcaster_django.models import EventConfig

EventConfig.objects.create(local_name="signup", remote_event_slug="user-signup")
```

then trigger the event by its local name through the `Client` facade:

```python
from bitcaster_django.client import Client

Client().trigger_event("signup", context={"username": user.username})
```

The event is triggered on the configured `PROJECT`/`APPLICATION`. Keeping the
mapping in the database decouples the names used in your code from the slugs
defined on the Bitcaster server, so they can be changed without redeploying.

### Managing users

The `Client` facade also wraps the sdk user management API. Application-level
membership (on the configured `PROJECT`/`APPLICATION`):

```python
from bitcaster_django.client import Client

client = Client()
client.register_user("username", "First", "Last", "user@example.com", active=True)
client.unregister_user("username")
```

and organization-level management:

```python
client.add_user("user@example.com", "First", "Last")
client.update_user("user@example.com", "First", "Last")
client.delete_user("user@example.com")
```

### Advanced clients

The `bitcaster_django.advanced` module provides drop-in subclasses of the
sdk clients — `Client` (sync) and `AsyncClient` — extended with a `django`
namespace of Django-aware helpers. Opt in via the `CLIENT` setting:

```python
BITCASTER = {
    ...
    "CLIENT": "bitcaster_django.advanced.Client",
    # or "bitcaster_django.advanced.AsyncClient"
}
```

The `django` namespace triggers events for a subset of the recipients, on
top of the sdk `trigger_event` API (the recipient filter travels in its
`options` parameter, any caller-provided options are preserved):

```python
from bitcaster_django.client import Client

sdk = Client().sdk  # the configured advanced client
sdk.set_domain("myprj", "myapp")

# only the users with the given usernames
sdk.django.trigger_for_users("user-signup", ["u1", "u2"], context={"k": "v"})

# only the users belonging to at least one of the given Django groups
sdk.django.trigger_for_groups("user-signup", [managers_group.pk])
```

`trigger_for_groups` resolves the group members to usernames using the
local Django database (the source of truth for the memberships synced to
Bitcaster — see the `groups` custom field above); the query always runs in
the calling thread, even with the async client. Both methods raise
`ValueError` on an empty recipient list (an empty filter could otherwise
reach every recipient), and return what the underlying client returns:
plain data for the sync client, `concurrent.futures.Future` objects for the
async one.

### Using the sdk directly

The `bitcaster_sdk` client is initialized automatically when Django starts, so
the [bitcaster-sdk](https://github.com/bitcaster-io/bitcaster-sdk) API can also
be used directly anywhere in your code — no `bitcaster_sdk.init()` call needed:

```python
import bitcaster_sdk

bitcaster_sdk.ping()
bitcaster_sdk.list_users()
```

### User synchronisation

When `SYNC_USERS` is enabled (the default), `post_save`/`post_delete` handlers
on your `AUTH_USER_MODEL` keep Bitcaster aligned with your Django users for
their whole lifecycle, using the username (`get_username()`) as the lookup
key. `PROJECT` and `APPLICATION` must be configured (enforced by the system
checks).

* Saving a Django user registers it as member of the configured
  `PROJECT`/`APPLICATION`, creating the Bitcaster user when missing and
  updating the membership otherwise — the same idempotent call covers
  creation, update, deactivation and reactivation.
* The membership `active` flag mirrors the user's `is_active`, so
  deactivating a Django user suspends it in Bitcaster without losing any
  Bitcaster-side data; user models without an `is_active` attribute are
  treated as always active.
* When the user has an email address, it is registered as an address assigned
  to the preferred channels, and the resulting assignments are subscribed to
  the `DISTRIBUTION_LIST` distribution list (when configured). Users without
  an email are registered without addresses.
* Deleting a Django user unregisters it, deleting its application membership
  records.

#### Targeting Django groups with Bitcaster filters

The membership custom fields always carry the pks of the Django groups the
user is assigned to, as a `dict[str, list[int]]`:

```json
{"groups": [3, 8, 11]}
```

The mapping is kept up to date as users are added to or removed from groups
(from either side of the relation: `user.groups.add(...)` or
`group.user_set.add(...)`). Since Bitcaster filter payloads can match the
membership custom fields, this lets a notification target only the users
belonging to a certain Django group — e.g. filtering on `groups` containing
the pk of your `managers` group sends the message to the Django managers
only, without maintaining a dedicated distribution list.

Any error while talking to Bitcaster is logged (logger
`bitcaster_django.handlers`, including the username, to allow manual
reconciliation) but never breaks the saving or deletion of the Django user;
unregistering a user unknown to Bitcaster is not an error.

Known limitations:

* bulk operations (`QuerySet.update()`/`QuerySet.delete()`) do not emit
  per-instance signals, so they are not synced;
* the sdk only uses names and email when *creating* the Bitcaster user:
  renaming a user or changing its email does not propagate to an already
  existing Bitcaster user;
* unregistering a user does not remove its distribution-list subscriptions;
* clearing a group from its reverse side (`group.user_set.clear()`) provides
  no affected-user information, so the `groups` custom field of those users
  is not refreshed until their next save or group change.

### Runtime configuration with django-constance

Install the optional extra:

```bash
pip install bitcaster-django[constance]
```

then add `constance` to `INSTALLED_APPS` and declare the `BITCASTER` keys you
want to manage at runtime as `BITCASTER_<KEY>` constance keys:

```python
INSTALLED_APPS = [
    ...
    "constance",
    "bitcaster_django",
]

CONSTANCE_CONFIG = {
    "BITCASTER_BAE": ("", "Bitcaster Application Endpoint"),
}
```

Configuration resolution order:

1. constance `BITCASTER_<KEY>` key (when declared and non-empty)
2. the `BITCASTER` settings dictionary
3. built-in defaults
4. the environment variables, when the resolved value is empty
   (`BITCASTER_BAE`, `BITCASTER_PROJECT_SLUG`, `BITCASTER_APPLICATION` and
   `BITCASTER_DISTRIBUTION_LIST` for `BAE`, `PROJECT`, `APPLICATION` and
   `DISTRIBUTION_LIST` respectively)

The sdk client is reinitialized automatically whenever a `BITCASTER_*`
constance key is updated (`config_updated` signal), so the endpoint can be
changed from the admin without restarting the application. At startup the
client is initialized from the static settings; any value stored in constance
is picked up on the first request.
