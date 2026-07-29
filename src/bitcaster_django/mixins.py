"""
Mixins for interacting with the Bitcaster API.

Includes helper classes to simplify common operations such as user creation
and deletion via the Bitcaster client.
"""

from typing import Any

import requests

from bitcaster_django.client import Client


class BitcasterUserMixin:
    """Mixin for managing Bitcaster user resources via the API."""

    def __init__(self, email: str) -> None:
        """Initialize the mixin with a Bitcaster API client and user email."""
        self.client = Client()
        self.email = email

    def create(self) -> Any:  # noqa: ANN401
        """Create a Bitcaster user using the stored email."""
        return self.client.add_user(self.email)

    def delete(self) -> requests.Response:
        """Delete the Bitcaster user associated with the stored email."""
        return self.client.delete_user(self.email)
