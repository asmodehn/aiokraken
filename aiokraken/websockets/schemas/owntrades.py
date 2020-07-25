from marshmallow import fields, post_dump, post_load, pre_load

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

    tradeid: typing.Optional[str]  # trade id
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

    def strategy(self):
        from aiokraken.websockets.schemas.tests.strats.st_owntrade import st_owntradews
        return st_owntradews()


class ownTradeWSSchema(BaseSchema):
    # <pair_name> = pair name
    tradeid = fields.Str()
    ordertxid = fields.Str() 	# order responsible for execution of trade
    postxid = fields.Str()      # Position trade id
    posstatus = fields.Str(allow_none=True)    # Position status
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
    def flatten(self, data, **kwargs):
        assert isinstance(data, dict)
        assert len(data) == 1
        k, v = next(iter(data.items()))
        data = {'tradeid': k, **v}
        return data

    @post_load
    def build_model(self, data, **kwargs):
        return ownTradeWS(**data)

    @post_dump
    def id_as_key(self, data, **kwargs):
        tid = data.pop("tradeid")
        return {
            tid: data
        }

    def strategy(self):
        from aiokraken.websockets.schemas.tests.strats.st_owntrade import st_owntradewsdict
        return st_owntradewsdict()

