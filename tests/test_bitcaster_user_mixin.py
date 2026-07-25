from unittest.mock import patch

from bitcaster_django.mixins import BitcasterUserMixin


def test_user_create():
    with patch("bitcaster_django.client.Client.add_user") as add_user:
        BitcasterUserMixin(email="example@mail").create()

    add_user.assert_called_once_with("example@mail")


def test_user_delete():
    with patch("bitcaster_django.client.Client.delete_user") as delete_user:
        BitcasterUserMixin(email="example@mail").delete()

    delete_user.assert_called_once_with("example@mail")
