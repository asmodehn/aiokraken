import unittest

from aiokraken.websockets.schemas.ticker import MinOrder, MinTrade, DailyValue, TickerWS, TickerWSSchema
from hypothesis import given
from aiokraken.websockets.schemas.tests.strats.st_ticker import st_tickerws, st_tickerwsdict


class TestTicker(unittest.TestCase):

    @given(tkr = st_tickerws())
    def test_valid_strategy(self, tkr):
        assert isinstance(tkr, TickerWS)

        assert isinstance(tkr.ask, MinOrder)
        assert isinstance(tkr.bid, MinOrder)
        assert isinstance(tkr.last_trade_closed, MinTrade)
        assert isinstance(tkr.volume, DailyValue)
        assert isinstance(tkr.volume_weighted_average_price, DailyValue)
        assert isinstance(tkr.high, DailyValue)
        assert isinstance(tkr.number_of_trades, DailyValue)
        assert isinstance(tkr.low, DailyValue)
        assert isinstance(tkr.todays_opening, DailyValue)  # the only change from Ticker !!!!
        # assert isinstance(tkr.pairname, typing.Optional[str])  # todo test this

    @given(dtrd = st_tickerwsdict())
    def test_valid_dictstrategy(self, dtrd):

        sch = TickerWSSchema()
        inst = sch.load(dtrd)
        assert isinstance(inst, TickerWS)


if __name__ == '__main__':
    unittest.main()
