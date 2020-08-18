import time
import unittest
from parameterized import parameterized
import json
import marshmallow

from aiokraken.rest.schemas.payload import PayloadSchema
from aiokraken.rest.exceptions import AIOKrakenServerError, AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema


# TODO : mock a schema ?
class TestPayloadSchema(unittest.TestCase):

    def setUp(self) -> None:

        class AnswerSchema(BaseSchema):
            answer = marshmallow.fields.Int()

        self.schema = PayloadSchema(AnswerSchema)

    @parameterized.expand([
        # we make sure we are using a proper json string
        [json.dumps({'error': [], 'result':{'answer': 42}})],
    ])
    def test_load_result(self, payload):
        """ Verifying that expected data parses properly """
        parsed = self.schema.loads(payload)
        assert parsed == {'answer': 42}, parsed

    @parameterized.expand([
        # we make sure we are using a proper json string
        [json.dumps({'error': ['BOUH'], 'result':{'answer': 42}})],
    ])
    def test_load_error(self, payload):
        """ Verifying that expected data parses properly """
        with self.assertRaises(AIOKrakenServerError):
            self.schema.loads(payload)

    @parameterized.expand([
        # we make sure we are using a proper json string
        [json.dumps({"what": "isit"})],
    ])
    def test_load_fail(self, payload):
        """ Verifying that unexpected data fails properly """
        with self.assertRaises(AIOKrakenSchemaValidationException):
            self.schema.loads(payload)
