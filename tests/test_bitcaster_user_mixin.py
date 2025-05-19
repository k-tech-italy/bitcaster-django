from unittest.mock import patch

from bitcaster_django.mixins import BitcasterUserMixin


def test_user_create(monkeypatch):
    with patch('requests.request') as mocked_request:
        bitcaster_user_mixin = BitcasterUserMixin(email='example@mail')

        bitcaster_user_mixin.create()

        mocked_request.assert_called_once_with('post', 'http://dummyhost/api/o/dummyorg/u/',
                                               headers={'Authorization': 'Key dummytoken'},
                                               timeout=15, data={'email': 'example@mail'})

def test_user_delete(monkeypatch):
    with patch('requests.request') as mocked_request:
        bitcaster_user_mixin = BitcasterUserMixin(email='example@mail')

        bitcaster_user_mixin.delete()

        mocked_request.assert_called_once_with('delete', 'http://dummyhost/api/o/dummyorg/u/example@mail/',
                                               timeout=15, headers={'Authorization': 'Key dummytoken'})
