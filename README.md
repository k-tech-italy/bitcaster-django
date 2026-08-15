# bitcaster-django

<!--
[![Test](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/test.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/test.yml)
[![Lint](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/lint.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/lint.yml)
[![Documentation](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/docs.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/docs.yml)
[![codecov](https://codecov.io/github/k-tech-italy/bitcaster-django/graph/badge.svg?token=BNXEW4JAYF)](https://codecov.io/github/k-tech-italy/bitcaster-django)
-->


Bitcaster-django is a Django app for seamless integration with [Bitcaster](https://docs.bitcaster.io/), the system-to-user signal-to-message notification system.

## Features

* **Zero-configuration setup** — the `bitcaster_sdk` client is initialized
  automatically at startup from the `BITCASTER` settings dictionary (or the
  `BITCASTER_BAE` environment variable): no `bitcaster_sdk.init()` call needed.
* **Event triggering** — a `Client` facade triggers remote Bitcaster events by
  local name, using the `EventConfig` model to map local event names to remote
  event slugs.
* **User synchronisation** — Django users are automatically registered as
  members of your Bitcaster application for their whole lifecycle (creation,
  update, deactivation/reactivation and deletion), optionally subscribing
  them to a distribution list, with helper mixins for user management.
* **Advanced clients** — optional drop-in sdk client subclasses (sync and
  async) with Django-aware helpers to trigger events only for given
  usernames or Django groups.
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
      # project/application slugs used by Client.trigger_event()
      # (required when SYNC_USERS is enabled)
      "PROJECT": "myprj",
      "APPLICATION": "myapp",
      # distribution list synced users are subscribed to (optional)
      "DISTRIBUTION_LIST": "mylist",
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

## Triggering events

Map a local event name to a remote Bitcaster event slug with the `EventConfig`
model (e.g. from the Django admin), then trigger the event by its local name
through the `Client` facade:

```python
from bitcaster_django.client import Client

Client().trigger_event("signup", context={"username": user.username})
```

With `CLIENT` pointing at one of the advanced clients
(`bitcaster_django.advanced.Client` or
`bitcaster_django.advanced.AsyncClient`), events can be triggered for a
subset of the recipients through the `django` namespace:

```python
from bitcaster_django.client import Client

sdk = Client().sdk  # the configured advanced client
sdk.set_domain("myprj", "myapp")
sdk.django.trigger_for_users("user-signup", ["u1", "u2"])
sdk.django.trigger_for_groups("user-signup", [managers_group.pk])
```

See the [documentation](https://k-tech-italy.github.io/bitcaster-django/) for
details.

## User synchronisation

When `SYNC_USERS` is enabled (the default), signal handlers on your
`AUTH_USER_MODEL` keep Bitcaster aligned with your Django users, using the
username as the lookup key:

* saving a Django user registers it as member of the configured
  `PROJECT`/`APPLICATION` (creating the Bitcaster user if missing), with the
  membership `active` flag mirroring `is_active`, so deactivating and
  reactivating a user is reflected in Bitcaster without losing data;
* when the user has an email address, it is registered as an address assigned
  to the preferred channels, and subscribed to the `DISTRIBUTION_LIST`
  distribution list (when configured);
* the membership custom fields always carry the pks of the Django groups the
  user is assigned to (e.g. `{"groups": [3, 8, 11]}`), kept up to date as
  users are added to/removed from groups — use it with Bitcaster filter
  payloads to send messages only to the users belonging to a certain group;
* deleting a Django user unregisters it from the application.

Any error while talking to Bitcaster is logged but never breaks the saving or
deletion of the Django user. Known limitations: bulk operations
(`QuerySet.update()`/`QuerySet.delete()`) do not emit per-instance signals and
are not synced; name/email changes are not propagated to an already existing
Bitcaster user; unregistering does not remove distribution-list subscriptions.

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

Distributed under the KRM Source License, Version 1.1, Apache 2.0 Future
License: see [LICENSE.md](LICENSE.md).
