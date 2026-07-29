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
    # forwarded to bitcaster_sdk.init() (optional, default: False)
    "DEBUG": False,
    # keep Bitcaster users aligned with Django users (optional, default: True)
    "SYNC_USERS": True,
    # project/application slugs used by Client.trigger_event().
    # Fall back to the BITCASTER_PROJECT_SLUG / BITCASTER_APPLICATION
    # environment variables when empty/omitted.
    "PROJECT": "myprj",
    "APPLICATION": "myapp",
}
```

All keys except `BAE`, `SYNC_USERS`, `PROJECT` and `APPLICATION` are forwarded (lowercased) to
[`bitcaster_sdk.init()`](https://github.com/bitcaster-io/bitcaster-sdk), so any
bitcaster-sdk option can be configured from the dictionary.

The configuration is validated by the Django system check framework:

```bash
python manage.py check
```

## Usage

The `bitcaster_sdk` client is initialized automatically when Django starts:
just use the sdk API anywhere in your code:

```python
import bitcaster_sdk

bitcaster_sdk.trigger(project="myprj", application="myapp", event="signup", context={...})
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
3. the `BITCASTER_BAE` environment variable (`BAE` only)
4. built-in defaults

The sdk client is reinitialized automatically whenever a `BITCASTER_*`
constance key is updated (`config_updated` signal), so the endpoint can be
changed from the admin without restarting the application. At startup the
client is initialized from the static settings; any value stored in constance
is picked up on the first request.
