import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..kcurrency import KCurrency, KCurrencyStrategy, KCurrencyField, KCurrencyStringStrategy
from ...exceptions import AIOKrakenException
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestKCurrency(unittest.TestCase):

    def test_unknown(self):
        """simple error verification"""
        with self.assertRaises(ValueError):
            KCurrency('unknown')

    @given(KCurrencyStrategy())
    def test_enum(self, model):
        assert model.value in ['EUR', 'USD', 'CAD', 'KRW', 'JPY',
                               # TODO : deal with aliases properly
                               'XBT', 'XBT', 'ETC', 'ETC', 'XRP']


class TestOrderTypeField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KCurrencyField()

    @given(KCurrencyStringStrategy())
    def test_deserialize(self, typestr):
        c = self.field.deserialize(typestr)
        assert isinstance(c, KCurrency)

    @given(KCurrencyStrategy())
    def test_serialize(self, currency):
        c = self.field.serialize('t', {'t': currency})
        assert c == currency.value, c
