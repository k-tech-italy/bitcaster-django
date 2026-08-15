---
title: Demo application
---

# Demo application

The repository ships a runnable demo project
([`tests/demoapp`](https://github.com/k-tech-italy/bitcaster-django/tree/develop/tests/demoapp))
that exercises every bitcaster-django feature from the browser, with no code
to write: it doubles as the settings fixture for the test suite and as a
live playground against a real Bitcaster instance.

## Running it

From a repository checkout, point the app at your Bitcaster instance and
start the dev server:

```bash
export BITCASTER_BAE="https://<token>@<host>/api/o/<organization>/"
export BITCASTER_PROJECT_SLUG="<project>"
export BITCASTER_APPLICATION="<application>"
export BITCASTER_DISTRIBUTION_LIST="<list>"   # optional

uv run tests/demoapp/manage.py migrate
uv run tests/demoapp/manage.py createsuperuser  # for /admin/
uv run tests/demoapp/manage.py runserver
```

Without the environment variables the app still runs with placeholder
settings: the calls to Bitcaster fail, but every endpoint reports the error
as readable JSON instead of crashing, so the wiring can be explored offline.

Open <http://127.0.0.1:8000/> for a JSON index of all the demo endpoints
together with the currently resolved configuration.

## Feature walkthrough

### User synchronisation (auto register/unregister)

The user endpoints only touch the Django ORM — every Bitcaster call is
performed by the bitcaster-django signal handlers, which is exactly what the
demo illustrates. Watch the users appear and change on the Bitcaster side as
you go:

| Endpoint | Django action | Synced to Bitcaster |
|---|---|---|
| `/users/add/alice/?first_name=Alice` | create user | registered (active membership) |
| `/users/alice/update/?last_name=Smith` | save user | membership upserted |
| `/users/alice/groups/managers/add/` | add to group (created if missing) | `custom_fields = {"groups": [<pk>]}` |
| `/users/alice/groups/managers/remove/` | remove from group | `custom_fields` updated |
| `/users/alice/deactivate/` | `is_active = False` | membership marked inactive |
| `/users/alice/activate/` | `is_active = True` | membership marked active |
| `/users/alice/delete/` | delete user | unregistered |
| `/users/` | — | inspect the local state |

The same flows can be exercised from `/admin/` (Users, Groups): the sync is
driven by signals, not by the demo views.

### Event triggering

Map a local event name to a remote slug first (`/admin/` → Event configs),
or use the remote slug directly in the URL — the trigger endpoints resolve
the name through `EventConfig` and fall back to using it as the slug:

| Endpoint | Feature |
|---|---|
| `/trigger/signup/?key=value` | `Client` facade: local name via `EventConfig`, query string as event context |
| `/trigger/signup/users/?u=alice&u=bob` | advanced client `trigger_for_users`: only the given usernames |
| `/trigger/signup/groups/?g=managers&g=3` | advanced client `trigger_for_groups`: only the members of the given groups (by name or pk) |

The demo configures the [advanced client](usage.md#advanced-clients) by
default (`BITCASTER["CLIENT"] = "bitcaster_django.advanced.Client"`); set
`BITCASTER_CLIENT=bitcaster_sdk.client.Client` to see the explanatory error
returned when the plain sdk client is configured instead.

### Runtime configuration (django-constance)

From `/admin/constance/config/` the `BITCASTER_*` keys (BAE, project,
application, distribution list) can be changed at runtime: the sdk client is
reinitialized automatically, no restart needed.

### System checks

```bash
uv run tests/demoapp/manage.py check
```

Try unsetting one of the environment variables above (or breaking the BAE)
to see the `bitcaster_django.E00x` checks report the misconfiguration.
