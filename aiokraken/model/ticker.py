# https://www.kraken.com/features/websocket-api#message-ticker

from collections import namedtuple

""" A common data structure for a Ticker """


MinOrder = namedtuple('MinOrder', ['price', 'whole_lot_volume', 'lot_volume'])
MinTrade = namedtuple('MinTrade', ['price', 'lot_volume'])
DailyValue = namedtuple('DailyValue', ['today', 'last_24_hours'])

class Ticker:
    # TODO : dataclass ?
    def __init__(self, b, a, l, p, h, c, o, t, v):
        self.ask = MinOrder(*a)
        self.bid = MinOrder(*b)
        self.last_trade_closed = MinTrade(*c)
        self.volume = DailyValue(*v)
        self.volume_weighted_average_price = DailyValue(*p)
        self.high = DailyValue(*h)
        self.number_of_trades = DailyValue(*t)
        self.low = DailyValue(*l)
        self.todays_opening = o

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
        return f"ask:{self.ask.lot_volume}@{self.ask.price} bid:{self.ask.lot_volume}@{self.bid.price}"
