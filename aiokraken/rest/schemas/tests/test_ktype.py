import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..ktype import KTypeModel, KTypeField
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestTypeModel(unittest.TestCase):

    def test_unknown(self):
        with self.assertRaises(ValueError):
            KTypeModel('unknown')

    def test_buy(self):
        # TODO : hypothesis strategy
        self.model = KTypeModel('buy')
        assert self.model == KTypeModel.buy

    def test_sell(self):
        # TODO : hypothesis strategy
        self.model = KTypeModel('sell')
        assert self.model == KTypeModel.sell


class TestOrderTypeField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KTypeField()

    @parameterized.expand([
        # we make sure we are using a proper json string
        ['buy', KTypeModel.buy],
        ['sell', KTypeModel.sell],
    ])
    def test_deserialize(self, typestr, expectedmodel):
        t = self.field.deserialize(typestr)
        assert isinstance(t, KTypeModel)
        assert t is expectedmodel, t

    @parameterized.expand([
        # we make sure we are using a proper json string
        [KTypeModel.buy, 'buy'],
        [KTypeModel.sell, 'sell'],
    ])
    def test_serialize(self, typemodel, expectedstr):
        t = self.field.serialize('type', {'type': typemodel})
        assert t == expectedstr, t
