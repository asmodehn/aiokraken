import time
import unittest
from parameterized import parameterized
import json
import marshmallow

from ..order import OrderSchema, Order
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOrderSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = OrderSchema()

    @parameterized.expand([
        # we make sure we are using a proper json string
        [Order(
            pair='SMTHG/ELSE',
            volume='42',
        )],
    ])
    def test_dump_ok(self, model):
        """ Verifying that expected data parses properly """
        serialized = self.schema.dump(model)
        expected = {
            "oflags": ["fcib"],
            "pair": "SMTHG/ELSE",
            "close": None,
            "starttm": "0",
            "validate": True,
            "expiretm": "0",
            "volume": 42
        }
        # check equality on dicts with usual python types, but display strings.
        assert serialized == expected, print(str(serialized) + '\n' + str(expected))

    @parameterized.expand([
        # we make sure we are using a proper json string
        [Order(
            pair='SMTHG/ELSE',
            volume='ABCD',
        )],
    ])
    def test_dump_fail(self, model):
        """ Verifying that unexpected data fails properly """
        with self.assertRaises((AIOKrakenException, marshmallow.exceptions.ValidationError, ValueError)):
            self.schema.dump(model)



