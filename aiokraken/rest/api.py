import types
import urllib
import hashlib
import base64
import hmac
import time
import signal
import asyncio
from dataclasses import dataclass, asdict, field

import typing

if __package__:
    from .request import Request
    from ..utils import get_nonce, get_kraken_logger
    from .schemas.payload import PayloadSchema
    from .schemas.time import TimeSchema
    from .schemas.balance import BalanceSchema
    from .response import Response
else:
    from aiokraken.rest.request import Request
    from aiokraken.utils import get_nonce, get_kraken_logger
    from aiokraken.rest.schemas.payload import PayloadSchema
    from aiokraken.rest.schemas.time import TimeSchema
    from aiokraken.rest.response import Response


def private(api, key, secret):
    api.api_url = 'private/'

    # TODO :call function (arg) to grab them from somewhere...
    api.key = key
    api.secret = secret

    def request(self, endpoint, headers=None, data=None, expected=None):
        h = headers or {}
        d = data or {}
        r = Request(url=self.url + '/' + endpoint, headers=h, data=d, expected=expected)
        s = r.sign(key=key, secret = secret)
        return s

    api.request = types.MethodType(request, api)
    return api


class API:

    def __init__(self, URId):
        self.id = URId  # the id of this api (as in 'URI')
        self._parent = None
        self._subapis = dict()

    def __setitem__(self, key, value):
        assert isinstance(value, API)
        value._parent = self
        self._subapis[key] = value

    def __getitem__(self, item):
        return self._subapis[item]

    @property
    def url(self):
        """
        determine the full url of this API by climbing up the tree
        >>> api = API('base')
        >>> api['bob'] = API('bobby')
        >>> api.url
        'base'
        >>> api['bob'].url
        'base/bobby'
        """
        return (self._parent.url + '/' + self.id) if self._parent is not None else self.id


    def headers(self, endpoint= None):
        _headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
            )
        }

        return _headers

    def request(self, endpoint, headers=None, data=None, expected=None):
        h = headers or {}
        r = Request(url=self.url + '/' + endpoint, headers=h, data=data, expected=expected)

        return r


class Version(API):
    """ A somewhat specific API """
    def __init__(self, version='0'):
        super().__init__(URId=version)


class Host(API):
    """ A somewhat specific API """
    def __init__(self, hostname):
        super().__init__(URId=hostname)



class Server:

    def __init__(self, key=None, secret=None):
        # building the API structure as a dict
        self.API = Host(hostname='api.kraken.com')
        self.API['0'] = Version()
        self.API['0']['public'] = API('public')
        self.API['0']['private'] = private(api=API('private'), key=key, secret=secret)
        # TODO : do this declaratively ???

    ###SHORTCUTS FOR CLIENT
    @property
    def public(self):
        return self.API['0']['public']

    @property
    def private(self):
        return self.API['0']['private']

    ### REquests
    def time(self):
        return self.public.request('Time', data=None, expected=Response(status=200, schema=PayloadSchema(TimeSchema)))

    def balance(self):
        return self.private.request('Balance', data=None, expected=Response(status=200, schema=PayloadSchema(BalanceSchema)))




# API DEFINITION - TODO - see uplink maybe ?

# @kraken.resource(success = , error=)
# def time(headers, data):
#     return {
#         200: success,
#         400: error,
#     }

