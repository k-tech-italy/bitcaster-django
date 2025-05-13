"""Models for bitcaster-django."""

from django.db import models


class EventConfig(models.Model):
    local_name = models.CharField(unique=True)
    remote_event_slug = models.SlugField()

    def __str__(self):
        return self.local_name
