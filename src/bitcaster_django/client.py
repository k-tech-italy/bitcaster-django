"""Client module for triggering Bitcaster events.

This module defines a `Client` class that integrates with Bitcaster,
retrieving event configuration from the local database and triggering
remote events based on the provided event name.
"""

import os

import bitcaster_sdk
from django.shortcuts import get_object_or_404

from bitcaster_django.models import EventConfig


class Client:
    """
    Client responsible for triggering remote events via Bitcaster.

    Uses local event configuration stored in the database to map local event
    names to remote Bitcaster event slugs and sends the corresponding trigger.
    """

    def trigger_event(self, event_name: str) -> None:
        """Triggers a remote event in Bitcaster based on the given local event name."""
        mapping = get_object_or_404(EventConfig, local_name=event_name)
        bitcaster_sdk.init()
        from bitcaster_sdk import trigger

        project = os.getenv("BITCASTER_PROJECT_SLUG")
        application = os.getenv("BITCASTER_APPLICATION")

        if not project:
            raise RuntimeError("Missing required environment variable BITCASTER_PROJECT_SLUG")
        if not application:
            raise RuntimeError("Missing required environment variable BITCASTER_APPLICATION")

        trigger(project=project, application=application, event=mapping.remote_event_slug)
