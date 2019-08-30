import unittest
from parameterized import parameterized
import json
import marshmallow
import pandas as pd

if __package__:
    from ..ohlc import PairOHLCSchema
else:
    from aiokraken.rest.schemas.ohlc import PairOHLCSchema

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestOHLCSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = PairOHLCSchema('XXBTZEUR')

    @parameterized.expand([
        # we make sure we are using a proper json string
        [json.dumps({'XXBTZEUR': [[1567041720, '8750.0', '8755.8', '8749.9', '8755.7', '8754.0', '3.98795136', 27],
                                  [1567041780, '8755.7', '8755.7', '8753.7', '8755.7', '8755.2', '0.02458507', 2], ],
                     'last': 1567041780})],
    ])
    def test_load_ok(self, payload):
        """ Verifying that expected data parses properly """
        parsed = self.schema.loads(json_data=payload)
        assert 'XXBTZEUR' in parsed
        assert isinstance(parsed.get('XXBTZEUR'), pd.DataFrame)

    # @parameterized.expand([
    #     # we make sure we are using a proper json string
    #     [json.dumps({"what": "isit"})],
    #     [json.dumps({"event": 42})],
    #     [json.dumps({"event": "some_other_string"})],
    # ])
    # def test_load_fail(self, payload):
    #     """ Verifying that unexpected data fails properly """
    #     with self.assertRaises(marshmallow.exceptions.ValidationError):
    #         self.schema.loads(payload)


