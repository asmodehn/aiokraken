import unittest

from aiokraken.utils.timeindexeddataframe import TimeindexedDataframe
from parameterized import parameterized
import pandas as pd

if __package__:
    from ..ohlc import OHLC
    from ..indicator import EMA, ema
else:
    from aiokraken.model.ohlc import OHLC
    from aiokraken.model.indicator import EMA, ema

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestEMA(unittest.TestCase):

    @parameterized.expand([
        [pd.DataFrame(
            # TODO:   proper Time, proper currencies...
            [[1567039620, 8746.4, 8751.5, 8745.7, 8745.7, 8749.3, 0.09663298, 8],
             [1567039680, 8745.7, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540, 1]],
            # grab that from kraken documentation
            columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
        ), 1567041780,
            pd.DataFrame(
                # TODO:   proper Time, proper currencies...
                [
                    [1567039680, 8745.8, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540, 1],
                    # Not the value is a bit modified to trigger stitching...
                    [1567039720, 8746.6, 8751.4, 8745.3, 8745.4, 8748.1, 0.09663297, 3]],
                # grab that from kraken documentation
                columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
            ), 1567041780,
        ],
    ])
    def test_ema_signal_ok(self, df1, last1, df2, last2):
        ohlc = OHLC(data=df1, last=last1)

        import pandas.api.types as ptypes

        num_cols = ["open", "high", "low", "close", "vwap", "volume", "count"]
        assert all(ptypes.is_numeric_dtype(ohlc.dataframe[col]) for col in num_cols)

        ema0 = ema(name="EMA1", length=1, offset=0, adjust=False)

        assert isinstance(ema0.timedataframe, TimeindexedDataframe)
        # TODO : check columns name
        assert len(ema0.timedataframe) == 0

        ema1 = ema0(ohlc_df=ohlc)

        assert len(ema0.timedataframe) == 0
        assert len(ema1.timedataframe) == len(ohlc)

        ohlc2 = OHLC(data=df2, last=last2)

        stitched1 = ohlc.stitch(ohlc2)

        ema2 = ema1(ohlc_df=stitched1)
        assert len(ema1.timedataframe) == len(ohlc.dataframe)
        assert len(ema2.timedataframe) == len(stitched1.dataframe)

        # TODO : assert more stuff

        pass

    def test_ema_mul(self):
        raise NotImplementedError  # TODO

    def test_ema_getitem(self):
        raise NotImplementedError  # TODO

    def test_ema_len(self):
        raise NotImplementedError  # TODO


if __name__ == "__main__":
    unittest.main()
