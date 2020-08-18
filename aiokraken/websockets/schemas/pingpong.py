# <class 'dict'>: {'connectionID': 12997236506998204415, 'event': 'systemStatus', 'status': 'online', 'version': '1.0.0'}


from dataclasses import dataclass

import typing

from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class Ping:
    reqid: int


@dataclass(frozen=True)
class Pong:
    reqid: int


class PingSchema(BaseSchema):
    """
    >>> s= PingSchema()
    >>> s.load({
    ... 'event': 'systemStatus',
    ... 'reqid': 42
    ... })
    Ping(reqid=42)
    """
    reqid = fields.Integer()
    event = fields.Constant("ping")

    @post_load
    def build_model(self, data, **kwargs):
        data.pop("event")
        a = Ping(**data)
        return a


class PongSchema(BaseSchema):
    """
    >>> s= PongSchema()
    >>> s.load({
    ... 'event': 'systemStatus',
    ... 'reqid': 42
    ... })
    Pong(reqid=42)
    """
    reqid = fields.Integer()
    event = fields.Constant("pong")

    @post_load
    def build_model(self, data, **kwargs):
        data.pop("event")
        a = Pong(**data)
        return a


if __name__ == '__main__':
    import doctest
    doctest.testmod()
