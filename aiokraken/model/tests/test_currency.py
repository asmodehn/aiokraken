import unittest

from hypothesis import given

from aiokraken.model.currency import KCurrency
from aiokraken.model.tests.strats.st_currency import KCurrencyStrategy


class TestKCurrency(unittest.TestCase):

    def test_unknown(self):
        """simple error verification"""
        with self.assertRaises(ValueError):
            KCurrency('unknown')

    @given(KCurrencyStrategy())
    def test_enum(self, model):
        assert model.value in ['EUR', 'USD', 'CAD', 'KRW', 'JPY',
                               # TODO : deal with aliases properly
                               'XBT', 'BTC', 'ETC', 'ETH', 'XRP', 'EOS', 'BCH', 'ADA', 'XTZ', 'BSV'], model.value


if __name__ == "__main__":
    unittest.main()