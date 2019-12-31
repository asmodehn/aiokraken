import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from ..ktm import TMModel, TimerField, TMStrategy, TimerStringStrategy
from ...exceptions import AIOKrakenException
from hypothesis import given, settings, Verbosity

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestTMModel(unittest.TestCase):

    def test_unknown(self):
        with self.assertRaises(ValueError):
            TMModel('unknown')

    # @settings(verbosity=Verbosity.verbose)
    @given(TMStrategy())
    def test_expired(self, model):
        if model.relative:
            assert str(model)[0] == '+'
            assert model.expired() == (model.value <= 0)  # not strict equivalence but what can we do without reference time?
        else:
            assert str(model)[0] != '+'
            assert model.expired() == (model.value > int(time.time())), int(time.time())


class TestTimerField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = TimerField()

    @given(TimerStringStrategy())
    def test_deserialize(self, ordertypestr):
        p = self.field.deserialize(ordertypestr)
        assert isinstance(p, TMModel)

    @given(TMStrategy())
    def test_serialize(self, tmmodel):
        tm = self.field.serialize('tm', {'tm': tmmodel})
        assert tm == str(tmmodel), tm
