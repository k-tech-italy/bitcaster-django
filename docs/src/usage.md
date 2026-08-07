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
    # project/application slugs used by Client.trigger_event().
    # Fall back to the BITCASTER_PROJECT_SLUG / BITCASTER_APPLICATION
    # environment variables when empty/omitted.
    "PROJECT": "myprj",
    "APPLICATION": "myapp",
    # fully qualified name of the sdk client class to use
    # (optional, default: "bitcaster_sdk.client.Client")
    "CLIENT": "bitcaster_sdk.async_client.AsyncClient",
}
```

All keys except `BAE`, `SYNC_USERS`, `PROJECT`, `APPLICATION` and `CLIENT` are
forwarded (lowercased) to the
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

Trigger an event defined on the Bitcaster server by its name through the
`Client` facade:

```python
from bitcaster_django.client import Client

Client().trigger_event("user-signup", context={"username": user.username})
```

The event is triggered on the configured `PROJECT`/`APPLICATION`.

### Managing users

The `Client` facade also wraps the sdk user management API:

```python
from bitcaster_django.client import Client

client = Client()
client.add_user("user@example.com", "First", "Last")
client.update_user("user@example.com", "First", "Last")
client.delete_user("user@example.com")
```

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

When `SYNC_USERS` is enabled (the default), a `post_save` handler on your
`AUTH_USER_MODEL` keeps Bitcaster users aligned with Django users:

* creating a Django user creates the matching Bitcaster user;
* updating a Django user updates it (creating it if missing).

Users without an email address are skipped, and any error while talking to
Bitcaster is logged (logger `bitcaster_django.handlers`) but never breaks the
saving of the Django user.

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
   (`BITCASTER_BAE`, `BITCASTER_PROJECT_SLUG` and `BITCASTER_APPLICATION` for
   `BAE`, `PROJECT` and `APPLICATION` respectively)

The sdk client is reinitialized automatically whenever a `BITCASTER_*`
constance key is updated (`config_updated` signal), so the endpoint can be
changed from the admin without restarting the application. At startup the
client is initialized from the static settings; any value stored in constance
is picked up on the first request.
