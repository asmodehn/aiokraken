import types

import marshmallow
from marshmallow import fields, pre_load, post_load

from ..exceptions import AIOKrakenException
from .base import BaseSchema
from .errors import ErrorsField
from .ohlc import OHLCDataFrameSchema
from .time import TimeSchema
""" Helper functions for dynamically building Schemas for payload"""


#  a runtime cache of schemas (class !) for different pairs
_payload_schemas = {}

def PayloadSchema(result_schema: BaseSchema):
    """helper function to create payload schemas for various results
        returns a new instance of the class, creating the class if needed.
    """

    def extract_result(self, data, **kwargs):
        assert len(data.get('error', [])) == 0  # Errors should have raised exception previously !
        return data.get('result')

    try:
        return _payload_schemas[result_schema]()
    except KeyError:
        _payload_schemas[result_schema] = type(f"Payload_{result_schema}", (BaseSchema,), {
            'error': ErrorsField(),
            'result': fields.Nested(result_schema),
            'make_result': marshmallow.post_load(pass_many=False)(extract_result)
        })
    finally:
        return _payload_schemas[result_schema]()

# TODO : doctest with example schema

_payload_schemas_with_fields = {}

def PayloadSchemaWithField(result_field: fields.Field):
    """helper function to create payload schemas for various results
        returns a new instance of the class, creating the class if needed.
    """

    def extract_result(self, data, **kwargs):
        assert len(data.get('error', [])) == 0  # Errors should have raised exception previously !
        return data.get('result')

    try:
        return _payload_schemas_with_fields[result_field]()
    except KeyError:
        _payload_schemas_with_fields[result_field] = type(f"Payload_Result_{result_field}", (BaseSchema,), {
            'error': ErrorsField(),
            'result': result_field,
            'make_result': marshmallow.post_load(pass_many=False)(extract_result)
        })
    finally:
        return _payload_schemas_with_fields[result_field]()
