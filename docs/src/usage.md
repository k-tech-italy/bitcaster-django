---
title: Getting started
---

# How to use bitcaster-django

## Configuration

bitcaster-django is configured with environment variables:

| Variable                 | Required | Description                                                                     |
|--------------------------|----------|---------------------------------------------------------------------------------|
| `BITCASTER_BAE`          | yes      | Bitcaster Application Endpoint: `https://<token>@<host>/api/o/<organization>/`   |
| `BITCASTER_PROJECT_SLUG` | yes*     | Slug of the Bitcaster project the events belong to                               |
| `BITCASTER_APPLICATION`  | yes*     | Slug of the Bitcaster application the events belong to                           |

\* required to trigger events with `Client.trigger_event()`.

The BAE embeds the API token, so treat it as a secret. A `RuntimeError` is
raised when `BITCASTER_BAE` is missing or does not match the expected format
(note the trailing slash after the organization).

## Usage

### Triggering events

Bitcaster events are triggered by a **local name**, decoupled from the remote
event slug. The mapping lives in the `EventConfig` model
(`local_name` → `remote_event_slug`); create the mappings from the Django
admin, a data migration, or the shell:

```python
from bitcaster_django.models import EventConfig

EventConfig.objects.create(local_name="user-signed-up", remote_event_slug="signup")
```

then trigger the remote event by its local name:

```python
from bitcaster_django.client import Client

client = Client()
client.trigger_event("user-signed-up")
```

`trigger_event()` resolves the local name to the remote slug and triggers the
event on the project/application identified by `BITCASTER_PROJECT_SLUG` and
`BITCASTER_APPLICATION`.

### Managing Bitcaster users

`BitcasterUserMixin` wraps the Bitcaster user API, keyed by email:

```python
from bitcaster_django.mixins import BitcasterUserMixin

user = BitcasterUserMixin(email="jane@example.com")
user.create()   # create the Bitcaster user
user.delete()   # delete the Bitcaster user
```

### Low-level API access

For endpoints not covered above, `Client` exposes authenticated helpers that
return the raw `requests.Response`, with paths relative to the organization
(`/api/o/<organization>`):

```python
client = Client()
client.get("/u/")                              # list users
client.post("/u/", data={"email": "jane@example.com"})
client.put(...)
client.delete("/u/jane@example.com/")
```
