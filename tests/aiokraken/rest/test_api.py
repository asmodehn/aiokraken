import pytest

from aiokraken.rest.api import API, Server


""" Test module for API structure """


def test_api_as_dict_behavior():

    api = API('base')
    api['bob'] = API('bobby')

    assert api.url == 'base'
    assert api['bob'].url == 'base/bobby'

# TODO  : test public and private request


def test_server():

    s = Server()
    assert s.public.url == 'api.kraken.com/0/public'
    assert s.private.url == 'api.kraken.com/0/private'






if __name__ == '__main__':
    pytest.main(['-s', __file__])
