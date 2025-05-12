import django
import pytest

import bitcaster_sdk
from bitcaster_django.client import Client

from unittest.mock import patch

from bitcaster_django.models import EventConfig


@pytest.mark.django_db
def test_trigger_event(monkeypatch):

    bitcaster_sdk.init()
    client = Client()
    with patch('bitcaster_sdk.trigger') as mock_trigger:
        monkeypatch.setenv('BITCASTER_PROJECT_SLUG', 'example_project')
        monkeypatch.setenv('BITCASTER_APPLICATION', 'example_application')

        EventConfig.objects.create(
            local_name='example_local_name', remote_event_slug='example_remote_slug')

        client.trigger_event('example_local_name')

        mock_trigger.assert_called_once_with(
            project='example_project', application='example_application',
        event='example_remote_slug')

@pytest.mark.parametrize(
    'env_variable', [
        ('BITCASTER_PROJECT_SLUG'),
        ('BITCASTER_APPLICATION')
    ]
)
@pytest.mark.django_db
def test_trigger_event_without_env_variables(monkeypatch, env_variable):

    bitcaster_sdk.init()
    client = Client()
    with patch('bitcaster_sdk.trigger'):
        monkeypatch.setenv('BITCASTER_PROJECT_SLUG', 'example_project')
        monkeypatch.setenv('BITCASTER_APPLICATION', 'example_application')
        monkeypatch.delenv(env_variable, False)

        EventConfig.objects.create(
            local_name='example_local_name', remote_event_slug='example_remote_slug')

        with pytest.raises(RuntimeError, match=f'Missing required environment variable {env_variable}'):
            client.trigger_event('example_local_name')
