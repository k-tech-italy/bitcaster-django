"""Admin for Bitcaster Django."""

from django.contrib import admin

from bitcaster_django.models import EventConfig


@admin.register(EventConfig)
class EventConfigAdmin(admin.ModelAdmin):
    """Admin for EventConfig."""

    list_display = ("local_name", "remote_event_slug")
