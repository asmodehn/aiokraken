import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..ping import KPingModel, KPingStrategy, KPingField, KPingStringStrategy
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestPingModel(unittest.TestCase):

    def test_unknown(self):
        """simple error verification"""
        with self.assertRaises(ValueError):
            KPingModel('unknown')

    @given(KPingStrategy())
    def test_enum(self, model):
        assert model.value in ['ping']


class TestPingField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KPingField()

    @given(KPingStringStrategy())
    def test_deserialize(self, typestr):
        t = self.field.deserialize(typestr)
        assert isinstance(t, KPingModel)

    @given(KPingStrategy())
    def test_serialize(self, typemodel):
        t = self.field.serialize('t', {'t': typemodel})
        assert t == typemodel.value, t
