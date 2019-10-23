import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..ktype import KTypeModel, KTypeField, KTypeStrategy, KTypeStringStrategy
from ...exceptions import AIOKrakenException
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestTypeModel(unittest.TestCase):

    def test_unknown(self):
        """simple error verification"""
        with self.assertRaises(ValueError):
            KTypeModel('unknown')

    @given(KTypeStrategy())
    def test_enum(self, model):
        # TODO : hypothesis strategy
        assert str(model) in ['buy', 'sell']


class TestOrderTypeField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KTypeField()

    @given(KTypeStringStrategy())
    def test_deserialize(self, typestr):
        t = self.field.deserialize(typestr)
        assert isinstance(t, KTypeModel)

    @given(KTypeStrategy())
    def test_serialize(self, typemodel):
        t = self.field.serialize('t', {'t': typemodel})
        assert t == str(typemodel), t
