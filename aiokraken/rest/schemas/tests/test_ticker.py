import time
import unittest
from parameterized import parameterized
import json
import marshmallow
from decimal import Decimal
from pprint import pprint, pformat

from ..ticker import TickerSchema, Ticker, DailyValue, MinOrder, MinTrade
from ...exceptions import AIOKrakenException

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestTickerSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = TickerSchema()

    @parameterized.expand([
        # we make sure we are using a proper json string
        [Ticker(
            ask= MinOrder(price=Decimal("7575.30000"), whole_lot_volume=Decimal("3"), lot_volume=Decimal("3.000")),
            bid= MinOrder(price=Decimal("7575.20000"), whole_lot_volume=Decimal("1"), lot_volume=Decimal("1.000")),
            last_trade_closed= MinTrade(price=Decimal("7575.20000"), lot_volume=Decimal("0.00624496")),
            volume= DailyValue(today=Decimal("458.99393133"), last_24_hours=Decimal("2687.78109961")),
            volume_weighted_average_price= DailyValue(today=Decimal("7570.63419"), last_24_hours=Decimal("7557.92793")),
            high= DailyValue(today=Decimal("7605.20000"), last_24_hours=Decimal("7625.20000")),
            number_of_trades= DailyValue(today=3146, last_24_hours=14600),
            low= DailyValue(today=Decimal("7488.30000"), last_24_hours=Decimal("7451.00000")),
            todays_opening= Decimal("7493.20000")
        )],
    ])
    def test_dump_ok(self, model):
        """ Verifying that expected data serializes properly """
        serialized = self.schema.dump(model)
        expected = {"a":["7575.30000","3","3.000"],
                    "b":["7575.20000","1","1.000"],
                    "c":["7575.20000","0.00624496"],
                    "v":["458.99393133","2687.78109961"],
                    "p":["7570.63419","7557.92793"],
                    "t":[3146,14600],
                    "l":["7488.30000","7451.00000"],
                    "h":["7605.20000","7625.20000"],
                    "o":"7493.20000"
                    }
        # check equality on dicts with usual python types, but display strings.
        assert serialized == expected, print(str({sk: sv for sk, sv in serialized.items() if expected.get(sk) != sv})
                                             + '\n' +
                                             str({ek: ev for ek, ev in expected.items() if serialized.get(ek) != ev}))

    @parameterized.expand([
        # we make sure we are using a proper json string
        [{"a":["7575.30000","3","3.000"],
         "b":["7575.20000","1","1.000"],
         "c":["7575.20000","0.00624496"],
         "v":["458.99393133","2687.78109961"],
         "p":["7570.63419","7557.92793"],
         "t":[3146,14600],
         "l":["7488.30000","7451.00000"],
         "h":["7605.20000","7625.20000"],
         "o":"7493.20000"}],
    ])
    def test_load_ok(self, data):
        """ Verifying that expected data parses properly """
        model = self.schema.load(data)
        expected = Ticker(
            ask= MinOrder(price=Decimal("7575.30000"), whole_lot_volume=Decimal("3"), lot_volume=Decimal("3.000")),
            bid= MinOrder(price=Decimal("7575.20000"), whole_lot_volume=Decimal("1"), lot_volume=Decimal("1.000")),
            last_trade_closed= MinTrade(price=Decimal("7575.20000"), lot_volume=Decimal("0.00624496")),
            volume= DailyValue(today=Decimal("458.99393133"), last_24_hours=Decimal("2687.78109961")),
            volume_weighted_average_price= DailyValue(today=Decimal("7570.63419"), last_24_hours=Decimal("7557.92793")),
            high= DailyValue(today=Decimal("7605.20000"), last_24_hours=Decimal("7625.20000")),
            number_of_trades= DailyValue(today=3146, last_24_hours=14600),
            low= DailyValue(today=Decimal("7488.30000"), last_24_hours=Decimal("7451.00000")),
            todays_opening= Decimal("7493.20000")
        )
        # check equality on dicts with usual python types, but display strings.
        assert model == expected, print(repr(model) + '\n' + repr(expected))


if __name__ == '__main__':
    unittest.main()
