import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.kcurrency import (
    KCurrency, KCurrencyStrategy, KCurrencyField, KCurrencyStringStrategy,
    KCurrencyStringAliasStrategy,
)
from aiokraken.rest.exceptions import AIOKrakenException
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""

class TestCurrencyField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KCurrencyField()

    @given(KCurrencyStringStrategy())
    def test_deserialize(self, typestr):
        c = self.field.deserialize(typestr)
        assert isinstance(c, KCurrency)

    @given(KCurrencyStringAliasStrategy())
    def test_deserialize_alias(self, typestr):
        c = self.field.deserialize(typestr)
        assert isinstance(c, KCurrency)

    @given(KCurrencyStrategy())
    def test_serialize(self, currency):
        c = self.field.serialize('t', {'t': currency})
        assert c == currency.value, c
