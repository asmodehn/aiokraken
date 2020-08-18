from datetime import datetime, timedelta, timezone

import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.ktm import (
    AbsoluteTimeSerializedStrategy, AbsoluteTimeStrategy, RelativeTimeSerializedStrategy, RelativeTimeStrategy,
    TimerField,
)
from aiokraken.rest.exceptions import AIOKrakenException
from hypothesis import given, settings, Verbosity

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestTimerField(unittest.TestCase):

    def setUp(self) -> None:
        self.field = TimerField()

    @given(RelativeTimeSerializedStrategy())  # because user may pass a string (relative input)
    def test_deserialize_relative(self, reltime):
        p = self.field.deserialize(reltime)
        assert isinstance(p, timedelta)
        assert p == timedelta(seconds=float(reltime[1:]))

    @given(AbsoluteTimeSerializedStrategy())  # because data is usually a float
    def test_deserialize_absolute(self, abstime):
        p = self.field.deserialize(abstime)
        assert isinstance(p, datetime)
        assert p == datetime.fromtimestamp(abstime, tz=timezone.utc)

    @given(RelativeTimeStrategy())
    def test_serialize_relative(self, reltime):
        tm = self.field.serialize('tm', {'tm': reltime})
        assert isinstance(tm, str)
        assert tm == f'+{reltime.total_seconds()}'

    @given(AbsoluteTimeStrategy())
    def test_serialize_absolute(self, abstime):
        tm = self.field.serialize('tm', {'tm': abstime})
        assert isinstance(tm, float)
        assert tm == abstime.timestamp()
