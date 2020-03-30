from dataclasses import dataclass

import typing

from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class Heartbeat:
    pass

class HeartbeatSchema(BaseSchema):
    """
    >>> s= HeartbeatSchema()
    >>> s.load({
    ... 'event': 'heartbeat',
    ... })
    HeartBeat
    """
    event = fields.Constant("heartbeat")

    @post_load
    def build_model(self, data, **kwargs):
        data.pop("event")  # nothing left
        a = Heartbeat()
        return a


if __name__ == '__main__':
    import doctest
    doctest.testmod()
