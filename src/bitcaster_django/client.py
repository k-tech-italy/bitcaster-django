import os

import bitcaster_sdk
from django.shortcuts import get_object_or_404

from bitcaster_django.models import EventConfig


class Client:
    def trigger_event(self, event_name: str):
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
