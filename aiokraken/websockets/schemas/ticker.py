from marshmallow import post_load

from aiokraken.rest.schemas.base import BaseSchema

from aiokraken.model.ticker import  DailyValue, MinTrade, MinOrder
from aiokraken.rest.schemas.ticker import Ticker, DailyValueField, MinOrderField, MinTradeField


# TODO : careful here ticker model is slightly out of sync with th REST model
#   => factorize both as simply as possible...

# https://www.kraken.com/features/websocket-api#message-ticker

from collections import namedtuple
from dataclasses import dataclass, field, asdict
from decimal import Decimal

import typing


""" A common data structure for a Ticker """

# TODO : ticker timeindexed frame ?
@dataclass(frozen=True, init=True)
class TickerWS:
    ask: MinOrder
    bid: MinOrder
    last_trade_closed: MinTrade
    volume: DailyValue
    volume_weighted_average_price: DailyValue
    high: DailyValue
    number_of_trades: DailyValue
    low: DailyValue
    todays_opening: DailyValue  # the only change from Ticker !!!!
    pairname: typing.Optional[str] = field(default=None)  # this will be set a bit after initialization

    # def __init__(self, b, a, l, p, h, c, o, t, v):
    #     self.ask = MinOrder(*a)
    #     self.bid = MinOrder(*b)
    #     self.last_trade_closed = MinTrade(*c)
    #     self.volume = DailyValue(*v)
    #     self.volume_weighted_average_price = DailyValue(*p)
    #     self.high = DailyValue(*h)
    #     self.number_of_trades = DailyValue(*t)
    #     self.low = DailyValue(*l)
    #     self.todays_opening = o

    # a = ask array(<price>, <whole lot volume>, <lot volume>),
    # b = bid array(<price>, <whole lot volume>, <lot volume>),
    # c = last trade closed array(<price>, <lot volume>),
    # v = volume array(<today>, <last 24 hours>),
    # p = volume weighted average price array(<today>, <last 24 hours>),
    # t = number of trades array(<today>, <last 24 hours>),
    # l = low array(<today>, <last 24 hours>),
    # h = high array(<today>, <last 24 hours>),
    # o = today's opening price

    def __call__(self, pairname):  # for late naming
        newdata = asdict(self)
        newdata.update({'pairname': pairname})
        return TickerWS(**newdata)

    def __repr__(self):
        # TODO : refine... andc ompare with REST model
        return f"{self.pairname}: ask {self.ask.lot_volume} @ {self.ask.price} - bid {self.bid.lot_volume} @ {self.bid.price}\n"\
               f"today's open {self.todays_opening} high {self.high.today} low {self.low.today} close {self.last_trade_closed} volume {self.volume}\n"\
               f"{self.number_of_trades.today} trades @ vol_avg_price {self.volume_weighted_average_price.today}\n"

    def strategy(self):
        from aiokraken.websockets.schemas.tests.strats.st_ticker import st_tickerws
        return st_tickerws()


class TickerWSSchema(BaseSchema):
    # <pair_name> = pair name
    # TODO : namedtuples with nested schema ?
    ask = MinOrderField(data_key='a', as_string=True)  # ask array(<price>, <whole lot volume>, <lot volume>),
    bid = MinOrderField(data_key='b', as_string=True)  #bid array(<price>, <whole lot volume>, <lot volume>),
    last_trade_closed = MinTradeField(data_key='c', as_string=True)  #last trade closed array(<price>, <lot volume>),
    volume = DailyValueField(data_key='v', as_string=True)  #volume array(<today>, <last 24 hours>),
    volume_weighted_average_price = DailyValueField(data_key='p', as_string=True)  #volume weighted average price array(<today>, <last 24 hours>),
    number_of_trades = DailyValueField(data_key='t', as_string=False)  #number of trades array(<today>, <last 24 hours>), # TODO : should be integer, not decimal
    low = DailyValueField(data_key='l', as_string=True)  #low array(<today>, <last 24 hours>),
    high = DailyValueField(data_key='h', as_string=True)  #high array(<today>, <last 24 hours>),
    todays_opening = DailyValueField(data_key='o', as_string=True)  #today's opening price

    @post_load
    def build_model(self, data, **kwargs):
        return TickerWS(**data)

    @staticmethod
    def strategy():
        from aiokraken.websockets.schemas.tests.strats.st_ticker import st_tickerwsdict
        return st_tickerwsdict()
