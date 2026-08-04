# bitcaster-django

<!--
[![Test](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/test.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/test.yml)
[![Lint](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/lint.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/lint.yml)
[![Documentation](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/docs.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/docs.yml)
[![codecov](https://codecov.io/github/k-tech-italy/bitcaster-django/graph/badge.svg?token=BNXEW4JAYF)](https://codecov.io/github/k-tech-italy/bitcaster-django)
-->


Bitcaster-django is a Django app for seamless integrating with [Bitcaster](https://docs.bitcaster.io/) system-to-user signal-to-message notification system.

## Features

* **Zero-configuration setup** — the `bitcaster_sdk` client is initialized
  automatically at startup from the `BITCASTER` settings dictionary (or the
  `BITCASTER_BAE` environment variable): no `bitcaster_sdk.init()` call needed.
* **Event triggering** — a `Client` facade triggers remote Bitcaster events by
  local name, using the `EventConfig` model to map local event names to remote
  event slugs.
* **User synchronisation** — Bitcaster users are kept aligned with your Django
  users automatically (creation and updates), with helper mixins for user
  management.
* **Runtime configuration** — with the optional `constance` extra, any
  `BITCASTER` setting can be changed at runtime through django-constance; the
  sdk client is reinitialized automatically on changes.
* **System checks** — the configuration is validated via Django's system check
  framework (`python manage.py check`).

## Dependencies

* Python 3.10 or later
* Django 4.2 or later


## Installation

* Install bitcaster-django using your package manager of choice, e.g. Pip:
  ```bash
  pip install bitcaster-django
  # or, with django-constance support for runtime configuration:
  pip install bitcaster-django[constance]
  ```

* Add bitcaster-django to `INSTALLED_APPS` in your `config/settings.py` file:
  ```python
  INSTALLED_APPS = (
      ...
      "bitcaster_django",
      ...
  )
  ```

* Configure the app with the `BITCASTER` dictionary in your `config/settings.py` file:
  ```python
  BITCASTER = {
      # Bitcaster Application Endpoint.
      # Falls back to the BITCASTER_BAE environment variable when empty/omitted.
      "BAE": "https://<token>@<host>/api/o/<organization>/",
      # forwarded to the sdk client (optional, default: False)
      "DEBUG": False,
      # keep Bitcaster users aligned with Django users (optional, default: True)
      "SYNC_USERS": True,
      # project/application slugs used by Client.trigger_event() (optional)
      "PROJECT": "myprj",
      "APPLICATION": "myapp",
      # fully qualified name of the sdk client class to use
      # (optional, default: "bitcaster_sdk.client.Client")
      "CLIENT": "bitcaster_sdk.async_client.AsyncClient",
  }
  ```
  The `bitcaster_sdk` client is initialized automatically at startup: no
  `bitcaster_sdk.init()` call is needed in your code.

* Check that your configuration is valid:
  ```bash
  python manage.py check
  ```

## User synchronisation

When `SYNC_USERS` is enabled (the default), a `post_save` handler on your
`AUTH_USER_MODEL` keeps Bitcaster users aligned with Django users:

* creating a Django user creates the matching Bitcaster user;
* updating a Django user updates it (creating it if missing).

Users without an email address are skipped, and any error while talking to
Bitcaster is logged but never breaks the saving of the Django user.

## Runtime configuration with django-constance (optional)

With the `constance` extra installed, any `BITCASTER` key can be overridden at
runtime by declaring a `BITCASTER_<KEY>` entry in `CONSTANCE_CONFIG`:

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

A non-empty constance value takes precedence over the `BITCASTER` dictionary,
and the sdk client is reinitialized automatically whenever a `BITCASTER_*`
constance key is updated.

## Bug reports and requests for enhancements

Please open an issue on the project's [issue tracker on GitHub](https://github.com/k-tech-italy/bitcaster-django/issues).

## Contributing to the project

See the [contribution guide](CONTRIBUTING.md).

## Licensing

All rights reserved.
