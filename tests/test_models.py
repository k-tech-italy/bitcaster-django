import pytest

from bitcaster_django.models import EventConfig


pytestmark = pytest.mark.django_db


def test_event_config_str() -> None:
    obj = EventConfig.objects.create(local_name="signup", remote_event_slug="user-signup")
    assert str(obj) == "signup"
    assert str(obj.remote_event_slug) == "user-signup"
