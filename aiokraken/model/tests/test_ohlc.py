import unittest
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
        [pd.DataFrame(
            # TODO:   proper Time, proper currencies...
            [[1567039620, 8746.4, 8751.5, 8745.7, 8745.7, 8749.3, 0.09663298, 8],
             [1567039680, 8745.7, 8747.3, 8745.7, 8747.3, 8747.3, 0.00929540, 1]],
            # grab that from kraken documentation
            columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
        ), 1567041780],
    ])
    def test_load_ok(self, df, last):
        """ Verifying that expected data parses properly """
        ohlc = OHLC(data=df, last=last)


        # TODO : assert stuff

        ohlc.macd(fast=1, slow=1, signal=1)
        # TODO : assert more stuff

        pass