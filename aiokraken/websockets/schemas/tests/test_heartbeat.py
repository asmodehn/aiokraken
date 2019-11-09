import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..heartbeat import KHeartbeatModel, KHeartbeatStrategy, KHeartbeatField, KHeartbeatStringStrategy
from hypothesis import given

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestHeartbeatModel(unittest.TestCase):

    def test_unknown(self):
        """simple error verification"""
        with self.assertRaises(ValueError):
            KHeartbeatModel('unknown')

    @given(KHeartbeatStrategy())
    def test_enum(self, model):
        assert model.value in ['heartbeat']


class TestHeartbeatField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = KHeartbeatField()

    @given(KHeartbeatStringStrategy())
    def test_deserialize(self, typestr):
        t = self.field.deserialize(typestr)
        assert isinstance(t, KHeartbeatModel)

    @given(KHeartbeatStrategy())
    def test_serialize(self, typemodel):
        t = self.field.serialize('t', {'t': typemodel})
        assert t == typemodel.value, t
