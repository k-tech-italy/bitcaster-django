"""Models for bitcaster-django."""

from django.db import models


class EventConfig(models.Model):
    """
    Model that maps a local event name to a remote Bitcaster event slug.

    Attributes:
        local_name (str): The unique name used locally to identify the event.
        remote_event_slug (str): The corresponding slug used by Bitcaster to trigger the event.

    """

    local_name = models.CharField(max_length=100, unique=True)
    remote_event_slug = models.SlugField(max_length=100)

    def __str__(self) -> str:
        return self.local_name
