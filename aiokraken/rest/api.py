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
    # TODO : find a clean way to do these imports, package or not...
    from .request import Request
    from ..utils import get_nonce, get_kraken_logger
    from .schemas.payload import PayloadSchema
    from .schemas.time import TimeSchema
    from .schemas.ohlc import PairOHLCSchema
    from .schemas.balance import BalanceSchema
    from .schemas.order import OrderSchema, AddOrderResponseSchema, CancelOrderResponseSchema, OpenOrdersResponseSchema
    from .schemas.ticker import TickerSchema, PairTickerSchema
    from .response import Response
    from ..model.ohlc import OHLC
    from ..model.order import (ask, bid, buy, sell, cancel, Order, MarketOrder, LimitOrder, TakeProfitOrder, StopLossOrder, TrailingStopOrder)
else:
    from aiokraken.rest.request import Request
    from aiokraken.utils import get_nonce, get_kraken_logger
    from aiokraken.rest.schemas.payload import PayloadSchema
    from aiokraken.rest.schemas.time import TimeSchema
    from aiokraken.rest.schemas.ohlc import PairOHLCSchema
    from aiokraken.rest.schemas.order import OrderSchema, AddOrderResponseSchema, CancelOrderResponseSchema, OpenOrdersResponseSchema
    from aiokraken.rest.schemas.ticker import PairTickerSchema
    from aiokraken.rest.response import Response
    from aiokraken.model.ohlc import OHLC


def private(api, key, secret):
    api.api_url = 'private/'

    # TODO :call function (arg) to grab them from somewhere...
    api.key = key
    api.secret = secret

    def request(self, endpoint, headers=None, data=None, expected=None):
        h = headers or {}
        d = data or {}
        r = Request(urlpath=self.url_path + '/' + endpoint, headers=h, data=d, expected=expected)
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

    @property
    def url_path(self):
        return (self._parent.url_path + '/' + self.id) if self._parent is not None else self.id

    def headers(self, endpoint= None):
        _headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
            )
        }

        return _headers

    def request(self, endpoint, headers=None, data=None, expected=None):
        h = headers or {}
        r = Request(urlpath=self.url_path + '/' + endpoint, headers=h, data=data, expected=expected)

        return r


class Version(API):
    """ A somewhat specific API """
    def __init__(self, version='0'):
        super().__init__(URId=version)


class Host(API):
    """ A somewhat specific API """
    def __init__(self, hostname):
        super().__init__(URId=hostname)

    @property
    def url_path(self):
        return ''  # for a host we do not want the hostname in hte url path

# Kraken specific
pairs_id = {
    'XBTEUR': 'XXBTZEUR',
    'ETHEUR': 'XETHZEUR'
}



class Server:
    # TODO : LOG actual requests. Important for usage and for testing...

    def __init__(self, key=None, secret=None):
        # building the API structure as a dict
        self.API = Host(hostname='api.kraken.com')  # TODO : pass as argument ?
        self.API['0'] = Version()
        self.API['0']['public'] = API('public')
        self.API['0']['private'] = private(api=API('private'), key=key, secret=secret)
        # TODO : do this declaratively ???

    @property
    def url(self):
        return self.API.url

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

    def ohlc(self, pair='XBTEUR'):  # TODO : use a model to typecheck pair symbols
        return self.public.request('OHLC',
                                   data={'pair': pair},
                                   expected=Response(status=200,
                                                     schema=PayloadSchema(
                                                        result_schema=PairOHLCSchema(
                                                            pair=pairs_id.get(pair, pair))
                                                        )
                                                     )
                                   )

    def balance(self):
        return self.private.request('Balance',
                                    data=None,
                                    expected=Response(status=200,
                                                      schema=PayloadSchema(
                                                          result_schema=BalanceSchema
                                                      ))
                                    )

    def ticker(self, pair='XBTEUR'):  # TODO : use a model to typecheck pair symbols
        return self.public.request('Ticker',
                                   data={'pair': pair},
                                   expected=Response(status=200,
                                                     schema=PayloadSchema(
                                                        result_schema=PairTickerSchema(
                                                            pair=pairs_id.get(pair, pair))
                                                        )
                                                     )
                                   )

    def openorders(self, trades=False, userref=None):
        data = {'trades': trades}
        if userref is not None:
            data.update({'userref': userref})
        return self.private.request('OpenOrders',
                                   data=data,
                                   expected=Response(status=200,
                                                     schema=PayloadSchema(
                                                        result_schema=OpenOrdersResponseSchema
                                                        )
                                                     )
                                   )

    def bid(self, order: Order):
        return self.private.request('AddOrder',
                                    data=OrderSchema().dump(bid(order)),
                                    expected=Response(status=200,
                                                      schema=PayloadSchema(
                                                          result_schema=AddOrderResponseSchema
                                                      ))
                                    )

    def ask(self, order: Order):
        return self.private.request('AddOrder',
                                    data=OrderSchema().dump(ask(order)),
                                    expected=Response(status=200,
                                                      schema=PayloadSchema(
                                                          result_schema=AddOrderResponseSchema
                                                      ))
                                    )

    def cancel(self, txid_userref):
        return self.private.request('CancelOrder',
                                    data={'txid': txid_userref},  # TODO : produce dict from marshmallow...
                                    expected = Response(status=200,
                                                        schema=PayloadSchema(
                                                            result_schema=CancelOrderResponseSchema
                                                        ))
                                )

# API DEFINITION - TODO

# @kraken.resource(success = , error=)
# def time(headers, data):
#     return {
#         200: success,
#         400: error,
#     }

