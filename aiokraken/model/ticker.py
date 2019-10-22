# https://www.kraken.com/features/websocket-api#message-ticker

from collections import namedtuple
from dataclasses import dataclass, field
from decimal import Decimal

""" A common data structure for a Ticker """


MinOrder = namedtuple('MinOrder', ['price', 'whole_lot_volume', 'lot_volume'])
MinTrade = namedtuple('MinTrade', ['price', 'lot_volume'])
DailyValue = namedtuple('DailyValue', ['today', 'last_24_hours'])
# TODO : data validation of these ?


@dataclass(frozen=True, init=True)
class Ticker:
    ask: MinOrder
    bid: MinOrder
    last_trade_closed: MinTrade
    volume: DailyValue
    volume_weighted_average_price: DailyValue
    high: DailyValue
    number_of_trades: DailyValue
    low: DailyValue
    todays_opening: Decimal

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

    def __repr__(self):
        # TODO : refine...
        return f"ask {self.ask.lot_volume} @ {self.ask.price} - bid {self.bid.lot_volume} @ {self.bid.price}"\
               f"today's open {self.todays_opening} high {self.high.today} low {self.low.today} close {self.last_trade_closed} volume {self.volume}"\
               f"{self.number_of_trades.today} trades @ vol_avg_price {self.volume_weighted_average_price.today}\n"
