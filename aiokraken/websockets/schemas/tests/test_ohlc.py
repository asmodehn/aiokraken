import unittest

from aiokraken.websockets.schemas.ohlc import OHLCUpdate
from hypothesis import given
from aiokraken.websockets.schemas.tests.strats.st_ohlc import st_ohlcupdate


class TestOHLC(unittest.TestCase):

    @given(ohlc = st_ohlcupdate())
    def test_valid_strategy(self, ohlc):
        assert isinstance(ohlc, OHLCUpdate)

        assert isinstance(ohlc.time, float)  # Time, seconds since epoch
        assert isinstance(ohlc.etime, float)  # End timestamp of the interval
        assert isinstance(ohlc.open, float)  # Decimal  # Open price at midnight UTC
        assert isinstance(ohlc.high, float)  # Decimal  # Intraday high price
        assert isinstance(ohlc.low, float)  # Decimal  # Intraday low price
        assert isinstance(ohlc.close, float)  # Decimal  # Closing price at midnight UTC
        assert isinstance(ohlc.vwap, float)  # Decimal  # Volume weighted average price
        assert isinstance(ohlc.volume, float)  # Decimal  # Accumulated volume today
        assert isinstance(ohlc.count, int)  # Number of trades today
        # assert isinstance(ohlc.pairname, typing.Optional[str])  # todo test this


if __name__ == '__main__':
    unittest.main()
