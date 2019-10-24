import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..ktype import KABTypeModel, KABTypeField, KABTypeStrategy, KABTypeStringStrategy
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
            KABTypeModel('unknown')

    @given(KABTypeStrategy())
    def test_enum(self, model):
        assert model.value in ['buy', 'sell']


class TestOrderTypeField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KABTypeField()

    @given(KABTypeStringStrategy())
    def test_deserialize(self, typestr):
        t = self.field.deserialize(typestr)
        assert isinstance(t, KABTypeModel)

    @given(KABTypeStrategy())
    def test_serialize(self, typemodel):
        t = self.field.serialize('t', {'t': typemodel})
        assert t == typemodel.value, t
