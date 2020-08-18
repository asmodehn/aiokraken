import unittest

from aiokraken.websockets.schemas.trade import TradeWS, TradeWSSchema
from hypothesis import given
from aiokraken.websockets.schemas.tests.strats.st_trade import st_tradews, st_tradewsdict


class TestTrade(unittest.TestCase):

    @given(trd = st_tradews())
    def test_valid_strategy(self, trd):
        assert isinstance(trd, TradeWS)

        assert isinstance(trd.price, float)
        assert isinstance(trd.volume, float)
        assert isinstance(trd.time, float)
        assert isinstance(trd.side, str)
        assert isinstance(trd.orderType, str)
        assert isinstance(trd.misc, str)
        # assert isinstance(trd.pairname, typing.Optional[str])  # todo test this

    @given(dtrd = st_tradewsdict())
    def test_valid_dictstrategy(self, dtrd):

        sch = TradeWSSchema()
        inst = sch.load(dtrd)
        assert isinstance(inst, TradeWS)


if __name__ == '__main__':
    unittest.main()
