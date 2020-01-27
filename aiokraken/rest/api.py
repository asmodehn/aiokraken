import types

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.rest.payloads import TickerPayloadSchema, AssetPayloadSchema, AssetPairPayloadSchema
from aiokraken.rest.schemas.kclosedorder import ClosedOrdersResponseSchema

if not __package__:
    __package__ = 'aiokraken.rest'

from .request import Request
from .schemas.payload import PayloadSchema
from .schemas.time import TimeSchema
from .schemas.ohlc import PairOHLCSchema
from .schemas.balance import BalanceSchema
from .schemas.trade_balance import TradeBalanceSchema
from .schemas.kopenorder import OpenOrdersResponseSchema
from .schemas.krequestorder import (
    RequestOrderFinalized, AddOrderResponseSchema, CancelOrderResponseSchema,
    RequestOrderSchema,
)
from .response import Response


# TODO : simplify :
#  Ref: https://support.kraken.com/hc/en-us/articles/360025174872-How-to-create-the-krakenapi-py-file

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


def private(api: API, key, secret):
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



class Server:
    # TODO : LOG actual requests. Important for usage and for testing...

    def __init__(self, key=None, secret=None):
        # building the API structure as a dict
        self.API = Host(hostname='api.kraken.com')  # TODO : pass as argument ?
        self.API['0'] = Version()
        self.API['0']['public'] = API('public')

        if key and secret:  # we only have private API access if we provide key and secret
            self.API['0']['private'] = private(api=API('private'), key=key, secret=secret)
        else:  # But we still need to have access simulated for replays (no key)
            self.API['0']['private'] = API('private')
        # TODO : do this declaratively ???

    @property
    def url(self):
        return self.API.url

    ### SHORTCUTS FOR CLIENT
    @property
    def public(self):
        return self.API['0']['public']

    @property
    def private(self):
        return self.API['0']['private']

    ### Requests
    def time(self):
        return self.public.request('Time', data=None, expected=Response(status=200, schema=PayloadSchema(TimeSchema)))

    def assets(self, assets=None): # TODO : use a model to typecheck pair symbols
        return self.public.request('Assets',
                                   data={
                                       # info = info to retrieve (optional):
                                       #     info = all info (default)
                                       # aclass = asset class (optional):
                                       #     currency (default)
                                       'asset': ",".join([str(a) for a in assets])
                                    } if assets else {},
                                   expected=Response(status=200,
                                                     schema=AssetPayloadSchema())
        )

    def assetpair(self, assets=None): # TODO : use a model to typecheck pair symbols
        return self.public.request('AssetPairs',
                                   data={
                                       # info = info to retrieve (optional):
                                       #     info = all info (default)
                                       #     leverage = leverage info
                                       #     fees = fees schedule
                                       #     margin = margin info
                                       'pair':   ",".join([str(a) for a in assets])  # comma delimited list of asset pairs to get info on (optional.  default = all)
                                   } if assets else {},
                                   expected=Response(status=200,
                                                     schema=AssetPairPayloadSchema())
        )

    def ohlc(self, pair, interval: KTimeFrameModel):
        return self.public.request('OHLC',
                                   data={'pair': pair, 'interval': int(interval)},
                                   expected=Response(status=200,
                                                     schema=PayloadSchema(
                                                        result_schema=PairOHLCSchema(
                                                            pair=pair)
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

    def trade_balance(self, asset= 'ZEUR'):
        return self.private.request('TradeBalance',
                                    data={
                                        # TODO : not working just yet (Invalid arguments)
                                        # aclass = asset class (optional):
                                        #     currency (default)
                                        #'asset': asset   # base asset used to determine balance (default = ZUSD)
                                    },
                                    expected=Response(status=200,
                                                      schema=PayloadSchema(
                                                          result_schema=TradeBalanceSchema
                                                      ))
                                    )

    def ticker(self, pairs=['XBTEUR']):  # TODO : use a model to typecheck pair symbols
        pair_alias = 'XXBTZEUR'  # TODO : fix this hardcoded stuff !!!!
        return self.public.request('Ticker',
                                   data={'pair': ",".join(pairs)},
                                   expected=Response(status=200,
                                                     schema=TickerPayloadSchema()
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

    def closedorders(self, trades=False, userref=None):
        data = {'trades': trades}

        # trades = whether or not to include trades in output (optional.  default = false)
        # userref = restrict results to given user reference id (optional)
        # start = starting unix timestamp or order tx id of results (optional.  exclusive)
        # end = ending unix timestamp or order tx id of results (optional.  inclusive)
        # ofs = result offset
        # closetime = which time to use (optional)
        #     open
        #     close
        #     both (default)

        if userref is not None:
            data.update({'userref': userref})
        return self.private.request('ClosedOrders',
                                   data=data,
                                   expected=Response(status=200,
                                                     schema=PayloadSchema(
                                                        result_schema=ClosedOrdersResponseSchema
                                                        )
                                                     )
                                   )


    def addorder(self, order: RequestOrderFinalized):
        data = RequestOrderSchema().dump(order)
        print(f"Serialized Order: {data}")
        return self.private.request('AddOrder',
                                    data=data,
                                    expected=Response(status=200,
                                                      schema=PayloadSchema(
                                                          result_schema=AddOrderResponseSchema
                                                      ))
                                    )

    def cancel(self, txid_userref):
        # TODO : integration tests !!! Kraken seems to temporary lockout by hanging on this one....
        return self.private.request('CancelOrder',
                                    data={'txid': txid_userref},  # TODO : produce dict from marshmallow...
                                    expected = Response(status=200,
                                                        schema=PayloadSchema(
                                                            result_schema=CancelOrderResponseSchema
                                                        ))
                                )

    #
    # def query_orders(self):
    #     pass
    #
    #
    # def trades_history(self):
    #     pass
    #
    # def query_trades(self):
    #     pass

# API DEFINITION - TODO

# @kraken.resource(success = , error=)
# def time(headers, data):
#     return {
#         200: success,
#         400: error,
#     }

