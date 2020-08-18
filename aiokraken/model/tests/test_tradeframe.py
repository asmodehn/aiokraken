import unittest
import pandas as pd
from datetime import timezone

from aiokraken.model.tradeframe import TradeFrame

from aiokraken.model.time import Time

from aiokraken.model.tests.strats.st_tradeframe import st_tradeframe
from hypothesis import given, settings, Verbosity, HealthCheck
from hypothesis.strategies import sampled_from


class TestTradeHistory(unittest.TestCase):

    @given(t=st_tradeframe())
    # @settings(verbosity=Verbosity.verbose)
    def test_init(self, t: TradeFrame):
        # make sure t and next_t is ordered is ordered
        assert t.dataframe.index.is_monotonic_increasing

        # TODO : more assert (dtype and more...)

    @given(t=st_tradeframe(), next_t=st_tradeframe())
    # @settings(verbosity=Verbosity.verbose)
    def test_stitch(self, t: TradeFrame, next_t: TradeFrame):

        # make sure t and next_t is ordered is ordered
        assert t.dataframe.index.is_monotonic_increasing
        assert next_t.dataframe.index.is_monotonic_increasing

        # attempt merge
        newt = t.stitch(next_t)

        assert len(newt) >= len(t) and len(newt) >= len(next_t)
        assert newt.dataframe.index.is_monotonic_increasing
        # TODO : more detailed properties ?


if __name__ == "__main__":
    unittest.main()
