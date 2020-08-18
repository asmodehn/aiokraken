import functools
import typing

from enum import IntEnum

from aiokraken.rest.schemas.base import BaseSchema
from marshmallow import fields, post_load
from hypothesis import given, strategies as st

if __package__:
    from ...utils.stringenum import StringEnum
else:
    from aiokraken.utils.stringenum import StringEnum

class KWebSocketTokenResponseSchema(BaseSchema):
    token = fields.Str()
    expires = fields.Int()

    @post_load
    def build_model(self, obj, many, partial):
        # we need to return only the token
        return obj['token']
        # ignoring expiration for now
        # it is probably simpler to connect and retrieve new token if auth failed ?


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
