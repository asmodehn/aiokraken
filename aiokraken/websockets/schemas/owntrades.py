from marshmallow import fields, post_load, pre_load

from aiokraken.rest.schemas.base import BaseSchema


# TODO : careful here ticker model is slightly out of sync with th REST model
#   => factorize both as simply as possible...

# https://www.kraken.com/features/websocket-api#message-ticker

from collections import namedtuple
from dataclasses import dataclass, field, asdict
from decimal import Decimal

import typing


""" A common data structure for a Ticker """

@dataclass(frozen=True, init=True)
class ownTradeWS:

    ordertxid: str 	# order responsible for execution of trade
    postxid: str      # Position trade id
    pair: str         # Asset pair
    time: float       # unix timestamp of trade
    type: str         # type of order (buy/sell)
    ordertype: str 	# order type
    price: float      # average price order was executed at (quote currency)
    cost: float       # total cost of order (quote currency)
    fee: float        # total fee (quote currency)
    vol: float        # volume (base currency)
    margin: float     # initial margin (quote currency)

    # seems to have been added recently (some trades dont have it, despite having a postxid...)
    posstatus: typing.Optional[str] = field(default=None)  # Position status

    tradeid: typing.Optional[str] = field(default=None)  # this will be set a bit after initialization

    def __call__(self, tradeid):
        newdata = asdict(self)
        newdata.update({'tradeid': tradeid})
        return ownTradeWS(**newdata)

    # @staticmethod
    # def strategy(self):
    #     from aiokraken.websockets.schemas.tests.strats.st_trade import st_tradews
    #     return st_tradews()




class ownTradeWSContentSchema(BaseSchema):
    # <pair_name> = pair name

    ordertxid = fields.Str() 	# order responsible for execution of trade
    postxid = fields.Str()      # Position trade id
    posstatus = fields.Str()    # Position status
    pair = fields.Str()         # Asset pair
    time = fields.Float()       # unix timestamp of trade
    type = fields.Str()         # type of order (buy/sell)
    ordertype = fields.Str() 	# order type
    price = fields.Float()      # average price order was executed at (quote currency)
    cost = fields.Float()       # total cost of order (quote currency)
    fee = fields.Float()        # total fee (quote currency)
    vol = fields.Float()        # volume (base currency)
    margin = fields.Float()     # initial margin (quote currency)

    @pre_load
    def cleanup(self, data, **kwargs):
        return data

    @post_load
    def build_model(self, data, **kwargs):
        return ownTradeWS(**data)

    # @staticmethod
    # def strategy():
    #     from aiokraken.websockets.schemas.tests.strats.st_trade import st_tradewsdict
    #     return st_tradewsdict()


class ownTradeWSSchema(BaseSchema):

    trade_id = fields.Str()
    trade_details = fields.Nested(ownTradeWSContentSchema())

    @pre_load
    def cleanup(self, data, many, **kwargs):
        assert len(data) == 1  # only one trade here
        # temporary structure to manage kraken dynamic dict style...
        k, v = next(iter(data.items()))
        return {'trade_id': k,
                'trade_details': v}

    @post_load
    def build_model(self, data, many, **kwargs):
        return data['trade_details'](data['trade_id'])
