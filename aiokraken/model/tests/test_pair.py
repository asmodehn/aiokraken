import unittest
from hypothesis import given, settings, Verbosity, HealthCheck
from hypothesis.strategies import sampled_from
from .. import pair


class TestPair(unittest.TestCase):
    @given(sampled_from(pair.Fiat))
    def test_fiat_currency(self, code: pair.Fiat):

        cur = pair.currency(str(code))

        assert str(code) == str(cur)
        assert repr(code) == repr(cur)
        assert code == cur
        assert code is cur

    @given(sampled_from(pair.Crypto))
    def test_crypto_currency(self, code: pair.Crypto):

        cur = pair.currency(str(code))

        assert str(cur) == str(code)
        assert repr(cur) == repr(code)
        assert cur == code
        assert cur is code

    @given(sampled_from(pair.Alt))
    def test_alt_currency(self, code: pair.Alt):

        cur = pair.currency(str(code))

        assert str(cur) == str(code)
        assert repr(cur) == repr(code)
        assert cur == code
        assert cur is code

    @given(sampled_from(["RAND", "str", "code"]))
    def test_unknown_currency(self, code: str):

        # Using unknown currency will trigger error
        with self.assertRaises(pair.CurrencyError):
            pair.currency(str(code))


# TODO : symbol test
# def test_symbol(base, quote):
#     pass


# s = Symbol.from_str("EUR/ETH")
# assert type(s) is Symbol
# print(s.base)
# assert type(s.base) is Currency and s.base == Currency("EUR")
# print(s.quote)
# assert type(s.quote) is Currency and s.quote == Currency("ETH")
# print(s)


if __name__ == "__main__":
    unittest.main()
