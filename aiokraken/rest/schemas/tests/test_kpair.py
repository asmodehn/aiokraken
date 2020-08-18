import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.kpair import PairModel, PairStrategy, PairStringStrategy, PairField, KCurrency, PairStringAliasStrategy
from aiokraken.rest.exceptions import AIOKrakenException
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestPairField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = PairField()

    @given(PairStringStrategy())
    def test_deserialize(self, pairstr):
        p = self.field.deserialize(pairstr)
        assert isinstance(p, PairModel)
        assert isinstance(p.base, KCurrency)
        assert isinstance(p.quote, KCurrency)

    @given(PairStringAliasStrategy())
    def test_deserialize_alias(self, pairstr):
        p = self.field.deserialize(pairstr)
        assert isinstance(p, PairModel)
        assert isinstance(p.base, KCurrency)
        assert isinstance(p.quote, KCurrency)

    @given(PairStrategy())
    def test_serialize(self, pairmodel):
        p = self.field.serialize('pair', {'pair': pairmodel})
        assert p == str(pairmodel), p
