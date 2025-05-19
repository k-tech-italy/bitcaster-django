"""Client module for triggering Bitcaster events.

This module defines a `Client` class that integrates with Bitcaster,
retrieving event configuration from the local database and triggering
remote events based on the provided event name.
"""

import os
import re
from typing import Any

import bitcaster_sdk
from django.shortcuts import get_object_or_404

from bitcaster_django.models import EventConfig
import requests

class Client:
    """
    Client responsible for triggering remote events via Bitcaster.

    Uses local event configuration stored in the database to map local event
    names to remote Bitcaster event slugs and sends the corresponding trigger.
    """

    def __init__(self) -> None:
        bitcaster_bae = os.getenv('BITCASTER_BAE')
        if not bitcaster_bae:
            raise RuntimeError('Missing required environment variable BITCASTER_BAE')

        match = re.match(r"https?:\/\/([^@]+)@([^\/]+)\/api\/o\/([^\/]+)\/", bitcaster_bae)

        if not match:
            raise RuntimeError('Invalid BITCASTER_BAE format')

        self.api_key= match.group(1)
        self.base_url = 'http://' + match.group(2)
        self.organization = match.group(3)


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

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response: # noqa: ANN401
        """Send an HTTP request to the Bitcaster API with authentication."""
        full_url = self.base_url + '/api/o/' + self.organization + path

        return requests.request(method, full_url,headers={
                                    'Authorization': f'Key {self.api_key}',
                                }, timeout=15, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response: # noqa: ANN401
        """Send a POST request to the Bitcaster API."""
        return self._request('post', path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response: # noqa: ANN401
        """Send a DELETE request to the Bitcaster API."""
        return self._request('delete', path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response: # noqa: ANN401
        """Send a PUT request to the Bitcaster API."""
        return self._request('put', path, **kwargs)

    def get(self, path: str, **kwargs: Any) -> requests.Response: # noqa: ANN401
        """Send a GET request to the Bitcaster API."""
        return self._request('get', path, **kwargs)
