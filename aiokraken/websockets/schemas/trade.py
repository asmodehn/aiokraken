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
class TradeWS:

    price: float  # Price
    volume: 	float #	Volume
    time: 	float 	# Time, seconds since epoch
    side: 	str  # Triggering order side, buy/sell
    orderType: 	str  # Triggering order type market/limit
    misc: 	str  # Miscellaneous
    pairname: typing.Optional[str] = field(default=None)  # this will be set a bit after initialization

    def __call__(self, pairname):  # for late naming
        newdata = asdict(self)
        newdata.update({'pairname': pairname})
        return TradeWS(**newdata)

    # @staticmethod
    # def strategy(self):
    #     from aiokraken.websockets.schemas.tests.strats.st_trade import st_tradews
    #     return st_tradews()


class TradeWSSchema(BaseSchema):
    # <pair_name> = pair name
    price= fields.Decimal(as_string=True)  # Price
    volume= fields.Decimal(as_string=True)  # Volume
    time= fields.Float(as_string=True)  # Time, seconds since epoch
    side= fields.Str()  # Triggering order side, buy/sell
    orderType= fields.Str()  # Triggering order type market/limit
    misc= fields.Str()  # Miscellaneous

    @pre_load
    def parse_raw2dict(self, data, **kwargs):
        # https://docs.kraken.com/websockets-beta/#message-trade
        #CAREFUL : for some reason there are 2 levels of array...
        return {
            'price': data[0][0],
            'volume': data[0][1],
            'time': data[0][2],
            'side': data[0][3],
            'orderType': data[0][4],
            'misc': data[0][5],
        }

    @post_load
    def build_model(self, data, **kwargs):
        return TradeWS(**data)

    # @staticmethod
    # def strategy():
    #     from aiokraken.websockets.schemas.tests.strats.st_trade import st_tradewsdict
    #     return st_tradewsdict()
