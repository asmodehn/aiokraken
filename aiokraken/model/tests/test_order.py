import unittest
from parameterized import parameterized

from ..order import (Order, MarketOrder, LimitOrder, StopLossOrder, TakeProfitOrder, )## more more more


class TestOrder(unittest.TestCase):

    @parameterized.expand([
        ['MYPAIR', 'Volume'],
    ])
    def test_init(self, pair, volume):
        o = Order(pair = pair, volume=volume, )
        assert o.validate
        assert o.pair == pair
        assert o.volume == volume


    # TODO : more more more !


class TestMarketOrder(unittest.TestCase):

    @parameterized.expand([
        ['MYPAIR', 'Volume'],
    ])
    def test_init(self, pair, volume):
        o = MarketOrder(pair=pair, volume=volume, )
        assert o.validate
        assert o.pair == pair
        assert o.volume == volume


class TestLimitOrder(unittest.TestCase):

    @parameterized.expand([
        ['MYPAIR', 'Volume', 'price'],
    ])
    def test_init(self, pair, volume, price):
        o = LimitOrder(pair=pair, volume=volume, limit_price=price )
        assert o.validate
        assert o.pair == pair
        assert o.volume == volume
        assert o.price == price