import unittest
from datetime import datetime, timezone

from parameterized import parameterized
import pandas as pd

if __package__:
    from ..ohlc import OHLC
else:
    from aiokraken.model.ohlc import OHLC

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOHLC(unittest.TestCase):

    @parameterized.expand([
        [pd.DataFrame(  # One with "time" columns (like data from outside)
            # TODO:   proper Time, proper currencies...
            [[1567039620, 8746.4, 8751.5, 8745.7, 8745.7, 8749.3, 0.09663298, 8],
             [1567039680, 8745.7, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540, 1]],
            # grab that from kraken documentation
            columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
        ), 1567041780],
        [pd.DataFrame(  # One with "datetime" column (like internal model)
            # TODO:   proper Time, proper currencies...
            [[datetime.fromtimestamp(1567039620, tz=timezone.utc), 8746.4, 8751.5, 8745.7, 8745.7, 8749.3, 0.09663298, 8],
             [datetime.fromtimestamp(1567039680, tz=timezone.utc), 8745.7, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540, 1]],
            # grab that from kraken documentation
            columns=["datetime", "open", "high", "low", "close", "vwap", "volume", "count"]
        ), 1567041780],
        [pd.DataFrame(  # One with "datetime" AND "time" column (like internal model)
            # TODO:   proper Time, proper currencies...
            [[1567039620, datetime.fromtimestamp(1567039620, tz=timezone.utc), 8746.4, 8751.5, 8745.7, 8745.7, 8749.3, 0.09663298,
              8],
             [1567039680, datetime.fromtimestamp(1567039680, tz=timezone.utc), 8745.7, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540,
              1]],
            # grab that from kraken documentation
            columns=["time", "datetime", "open", "high", "low", "close", "vwap", "volume", "count"]
        ), 1567041780],
    ])
    def test_load_ok(self, df, last):
        """ Verifying that expected data parses properly """
        ohlc = OHLC(data=df, last=last)

        import pandas.api.types as ptypes

        num_cols = ["open", "high", "low", "close", "vwap", "volume", "count"]
        assert all(ptypes.is_numeric_dtype(ohlc.dataframe[col]) for col in num_cols)

        assert ptypes.is_datetime64_any_dtype(ohlc.dataframe["datetime"])
        assert ohlc.dataframe.index.name == 'time'
        assert ohlc.dataframe.index.dtype == 'int64'

        # verifying date conversion to native (numpy precision not needed in our context)
        assert ohlc.dataframe["datetime"].iloc[0].to_pydatetime() == datetime(year=2019, month=8, day=29, hour=0, minute=47, second=0, tzinfo=timezone.utc), ohlc.dataframe["datetime"].iloc[0]

    # TODO : property test instead (move this example test to doc...)


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
             [1567039680, 8745.7, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540, 1],
             [1567039720, 8746.6, 8751.4, 8745.3, 8745.4, 8748.1, 0.09663297, 3]],
            # grab that from kraken documentation
            columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
        ), 1567041780,
        ],
    ])
    def test_ohlc_stitch(self, df1, last1, df2, last2):
        """ Verifying that expected data parses properly """
        ohlc1 = OHLC(data=df1, last=last1)
        ohlc2 = OHLC(data=df2, last=last2)

        stitched1 = ohlc1.stitch(ohlc2)

        import pandas.api.types as ptypes

        num_cols = ["open", "high", "low", "close", "vwap", "volume", "count"]
        assert all(ptypes.is_numeric_dtype(stitched1.dataframe[col]) for col in num_cols)

        assert ptypes.is_datetime64_any_dtype(stitched1.dataframe["datetime"])

        # verifying stitches
        assert (stitched1.dataframe.iloc[0] == ohlc1.dataframe.iloc[0]).all()
        assert (stitched1.dataframe.iloc[-1] == ohlc2.dataframe.iloc[-1]).all()

        assert len(stitched1) == 3

        # verifying order doesnt matter -> result is same.
        stitched2 = ohlc2.stitch(ohlc1)
        assert stitched1 == stitched2


if __name__ == "__main__":
    unittest.main()
