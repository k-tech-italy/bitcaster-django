---
title: Documentation
---

Bitcaster-django is a Django app that integrates your project with
[Bitcaster](https://docs.bitcaster.io/), the system-to-user signal-to-message
notification system: it lets you trigger remote Bitcaster events from local,
database-configured event names and manage Bitcaster users from your Django
application.


## Dependencies

* Python 3.10 or later
* Django 4.2 or any later version supporting your Python version of choice.


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

See [Getting started](usage.md) for configuration and usage.

## Bug reports and requests for enhancements

Please open an issue on the project's [issue tracker on GitHub](https://github.com/k-tech-italy/bitcaster-django/issues).

## Contributing to the project

See the [contribution guide](contributing.md).

## Licensing

All rights reserved.
