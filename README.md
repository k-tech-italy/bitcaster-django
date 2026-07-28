# bitcaster-django

<!--
[![Test](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/test.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/test.yml)
[![Lint](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/lint.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/lint.yml)
[![Documentation](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/docs.yml/badge.svg)](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/docs.yml)
[![codecov](https://codecov.io/github/k-tech-italy/bitcaster-django/graph/badge.svg?token=BNXEW4JAYF)](https://codecov.io/github/k-tech-italy/bitcaster-django)
-->

Bitcaster-django is a Django app that integrates your project with
[Bitcaster](https://docs.bitcaster.io/), the system-to-user signal-to-message
notification system: it lets you trigger remote Bitcaster events from local,
database-configured event names and manage Bitcaster users from your Django
application.


## Dependencies

* Python 3.8 or later
* Django 4.2 or later


## Installation

* Install bitcaster-django using your package manager of choice, e.g. Pip:
  ```bash
  pip install bitcaster-django
  ```

* Add bitcaster-django to `INSTALLED_APPS` in your `config/settings.py` file:
  ```python
  INSTALLED_APPS = (
      ...
      "bitcaster_django",
      ...
  )
  ```

* Run the migrations to create the event configuration table:
  ```bash
  python manage.py migrate
  ```

* Check that your configuration is valid:
  ```bash
  python manage.py check
  ```

## Configuration

The app is configured with environment variables:

| Variable                 | Required | Description                                                                        |
|--------------------------|----------|------------------------------------------------------------------------------------|
| `BITCASTER_BAE`          | yes      | Bitcaster Application Endpoint: `https://<token>@<host>/api/o/<organization>/`      |
| `BITCASTER_PROJECT_SLUG` | yes*     | Slug of the Bitcaster project the events belong to                                  |
| `BITCASTER_APPLICATION`  | yes*     | Slug of the Bitcaster application the events belong to                              |

\* required to trigger events with `Client.trigger_event()`.

## Usage

Map a local event name to a remote Bitcaster event slug with the `EventConfig`
model, then trigger it by its local name:

```python
from bitcaster_django.client import Client

Client().trigger_event("user-signed-up")
```

See the [documentation](https://k-tech-italy.github.io/bitcaster-django/) for
the full usage guide, including Bitcaster user management.

## Bug reports and requests for enhancements

Please open an issue on the project's [issue tracker on GitHub](https://github.com/k-tech-italy/bitcaster-django/issues).

## Contributing to the project

See the [contribution guide](CONTRIBUTING.md).
