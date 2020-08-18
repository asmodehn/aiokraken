import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.kordertype import KOrderTypeModel, KOrderTypeField, KOrderTypeStrategy, KOrderTypeStringStrategy
from aiokraken.rest.exceptions import AIOKrakenException
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOrderTypeModel(unittest.TestCase):

    def test_unknown(self):
        with self.assertRaises(ValueError):
            KOrderTypeModel('unknown')

    @given(KOrderTypeStrategy())
    def test_enum(self, model):
        assert model.value in [
            'market',
            'stop market',
            'touched market',
            'limit',
            'stop-loss',
            'take-profit',
            'stop-loss-profit',
            'stop-loss-profit-limit',
            'stop-loss-limit',
            'take-profit-limit',
            'trailing-stop',
            'trailing-stop-limit',
            'stop-loss-and-limit',
            'settle-position',
        ], model.value


class TestOrderTypeField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KOrderTypeField()

    @given(KOrderTypeStringStrategy())
    def test_deserialize(self, ordertypestr):
        p = self.field.deserialize(ordertypestr)
        assert isinstance(p, KOrderTypeModel)

    @given(KOrderTypeStrategy())
    def test_serialize(self, ordertypemodel):
        ot = self.field.serialize('ordertype', {'ordertype': ordertypemodel})
        assert ot == ordertypemodel.value, ot
