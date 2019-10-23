import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..kpair import PairModel, PairField, Currency, Fiat, Crypto, Alt
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestPairModel(unittest.TestCase):

    def setUp(self) -> None:
        # TODO : hypothesis strategy
        self.model = PairModel(base=Fiat.EUR, quote=Crypto.BTC)
        # some values are already accessible in model
        assert self.model.base is Fiat.EUR
        assert self.model.quote is Crypto.BTC

    def test_repr(self):
        assert repr(self.model) == f"{self.model.base}/{self.model.quote}"


class TestPairField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = PairField()

    @parameterized.expand([
        # we make sure we are using a proper json string
        ['EURBTC'],
    ])
    def test_deserialize(self, pairstr):
        p = self.field.deserialize(pairstr)
        assert isinstance(p, PairModel)
        assert p.base == Fiat.EUR
        assert p.quote == Crypto.BTC

    @parameterized.expand([
        # we make sure we are using a proper json string
        [PairModel(
            base=Fiat.EUR,
            quote=Crypto.BTC
        )],
    ])
    def test_serialize(self, pairmodel):
        p = self.field.serialize('pair', {'pair': pairmodel})
        assert p == 'EURBTC', p
