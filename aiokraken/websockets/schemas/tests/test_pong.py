import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..pong import KPongModel, KPongStrategy, KPongField, KPongStringStrategy
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestPongModel(unittest.TestCase):

    def test_unknown(self):
        """simple error verification"""
        with self.assertRaises(ValueError):
            KPongModel('unknown')

    @given(KPongStrategy())
    def test_enum(self, model):
        assert model.value in ['pong']


class TestPongField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KPongField()

    @given(KPongStringStrategy())
    def test_deserialize(self, typestr):
        t = self.field.deserialize(typestr)
        assert isinstance(t, KPongModel)

    @given(KPongStrategy())
    def test_serialize(self, typemodel):
        t = self.field.serialize('t', {'t': typemodel})
        assert t == typemodel.value, t
