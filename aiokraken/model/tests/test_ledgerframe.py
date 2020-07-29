import unittest
import pandas as pd
from datetime import timezone

from aiokraken.model.ledgerframe import LedgerFrame

from aiokraken.model.time import Time

from aiokraken.model.tests.strats.st_ledgerframe import st_ledgerframe
from hypothesis import given, settings, Verbosity, HealthCheck
from hypothesis.strategies import sampled_from


class TestLedger(unittest.TestCase):

    @given(l=st_ledgerframe())
    # @settings(verbosity=Verbosity.verbose)
    def test_init(self, l: LedgerFrame):
        # make sure t and next_t is ordered is ordered
        assert l.dataframe.index.is_monotonic_increasing

        # TODO : more assert (dtype and more...)

    @given(l=st_ledgerframe(), next_l=st_ledgerframe())
    # @settings(verbosity=Verbosity.verbose)
    def test_stitch(self, l: LedgerFrame, next_l: LedgerFrame):

        # make sure t and next_t is ordered is ordered
        assert l.dataframe.index.is_monotonic_increasing
        assert next_l.dataframe.index.is_monotonic_increasing

        # attempt merge
        newt = l.stitch(next_l)

        assert len(newt) >= len(l) and len(newt) >= len(next_l)
        assert newt.dataframe.index.is_monotonic_increasing
        # TODO : more detailed properties ?


if __name__ == "__main__":
    unittest.main()
