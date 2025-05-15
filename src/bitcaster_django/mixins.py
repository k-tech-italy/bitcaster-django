"""
Mixins for interacting with the Bitcaster API.

Includes helper classes to simplify common operations such as user creation
and deletion via the Bitcaster client.
"""
from src.bitcaster_django.client import Client
import requests

class BitcasterUserMixin:
    """Mixin for managing Bitcaster user resources via the API."""

    def __init__(self, email: str) -> None:
        """Initialize the mixin with a Bitcaster API client and user email."""
        self.client = Client()
        self.email = email

    def create(self) -> requests.Response:
        """Create a Bitcaster user using the stored email."""
        return self.client.post('/u/', data={'email': self.email})

    def delete(self) -> requests.Response:
        """Delete the Bitcaster user associated with the stored email."""
        return self.client.delete(f'/u/{self.email}')
