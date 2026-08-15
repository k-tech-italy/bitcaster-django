# bitcaster-django demo app

> Full walkthrough:
> [Demo application](https://k-tech-italy.github.io/bitcaster-django/demo/)
> on the documentation site (source: `docs/src/demo.md`).

A minimal Django project demonstrating every bitcaster-django feature:
automatic user registration/unregistration, group syncing, event triggering
through the `Client` facade, the advanced client's `trigger_for_users` /
`trigger_for_groups` helpers, system checks and runtime configuration via
django-constance.

## Run it

From the repository root, point the app at your Bitcaster instance and start
the dev server:

```bash
export BITCASTER_BAE="https://<token>@<host>/api/o/<organization>/"
export BITCASTER_PROJECT_SLUG="<project>"
export BITCASTER_APPLICATION="<application>"
export BITCASTER_DISTRIBUTION_LIST="<list>"   # optional

uv run tests/demoapp/manage.py migrate
uv run tests/demoapp/manage.py createsuperuser  # for /admin/
uv run tests/demoapp/manage.py runserver
```

Without the environment variables the app still runs (with placeholder
settings), but the calls to Bitcaster fail: the demo endpoints report the
error as JSON instead of crashing, so the wiring can be explored offline too.

Open <http://127.0.0.1:8000/> for a JSON index of all the demo endpoints and
the currently resolved configuration.

## What to try

**User lifecycle** (spec 001 — every step is mirrored to Bitcaster by the
signal handlers, watch the server side as you go):

```text
/users/add/alice/?first_name=Alice     create   -> register_user (active)
/users/alice/update/?last_name=Smith   update   -> re-register
/users/alice/groups/managers/add/      groups   -> custom_fields {"groups": [pk]}
/users/alice/deactivate/               disable  -> membership active=False
/users/alice/activate/                 enable   -> membership active=True
/users/alice/delete/                   delete   -> unregister_user
/users/                                inspect the local state
```

The same flows can be exercised from `/admin/` (users, groups): the sync is
driven by signals, not by the views.

**Event triggering** — map a local event name to a remote slug first (admin →
Event configs, or use the remote slug directly in the URL):

```text
/trigger/signup/?key=value             Client facade, local name via EventConfig
/trigger/signup/users/?u=alice&u=bob   advanced client: only these usernames
/trigger/signup/groups/?g=managers     advanced client: only these groups (pk or name)
```

The trigger endpoints require the advanced client (the demo default, see
`BITCASTER["CLIENT"]` in `demo/settings.py`); set
`BITCASTER_CLIENT=bitcaster_sdk.client.Client` to see the helpful error the
demo returns when the plain sdk client is configured instead.

**Runtime configuration** — with `/admin/constance/config/` any
`BITCASTER_*` key (BAE, project, application, distribution list) can be
changed at runtime: the sdk client is reinitialized automatically.

**System checks** — try `uv run tests/demoapp/manage.py check` after unsetting
one of the environment variables above.
