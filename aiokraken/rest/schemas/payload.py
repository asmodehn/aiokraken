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


def PayloadSchema(result_schema):
    """helper function to create payload schemas for various results
        returns a new instance of the class, creating the class if needed.
    """
    try:
        return _payload_schemas[result_schema]()
    except KeyError:
        _payload_schemas[result_schema] = type(f"Payload_{result_schema}", (BaseSchema,), {
            'error': ErrorsField(),
            'result': fields.Nested(result_schema)
        })
    finally:
        return _payload_schemas[result_schema]()

# TODO : doctest with example schema
