from dataclasses import dataclass, field

import typing

from marshmallow import fields, post_load, post_dump, pre_load, pre_dump


from aiokraken.rest.schemas.base import BaseSchema
from aiokraken.websockets.schemas.subscribe import Subscription, SubscriptionSchema


@dataclass(frozen=True)
class Unsubscribe:
    subscription: Subscription
    pair: typing.List[str]  # TODO : use pair with proper type
    reqid: typing.Optional[int] = field(default=None)


@dataclass(frozen=True)
class ChannelUnsubscribe:
    channel_id: int
    reqid: typing.Optional[int] = field(default=None)


class UnsubscribeSchema(BaseSchema):
    """
    >>> s= UnsubscribeSchema()
    >>> s.load({'event': 'unsubscribe',
    ... 'pair': ['XBT/USD'],
    ... 'subscription': {'name': 'ticker'}
    ... })
    Unsubscribe(subscription=Subscription(name='ticker', interval=None, depth=None, token=''), pair=['XBT/USD'], reqid=None)
    """
    event = fields.Constant("unsubscribe")
    reqid = fields.Integer()
    pair = fields.List(fields.String())
    subscription = fields.Nested(SubscriptionSchema())

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # not needed any longer
        a = Unsubscribe(**data)
        return a


class ChannelUnsubscribeSchema(BaseSchema):
    """
    >>> s= ChannelUnsubscribeSchema()
    >>> s.load({'event': 'unsubscribe',
    ... 'reqid': 39,
    ... 'channel_id': 142
    ... })
    ChannelUnsubscribe(channel_id=142, reqid=39)
    """
    event = fields.Constant("unsubscribe")
    reqid = fields.Integer()
    channel_id = fields.Integer()

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # not needed any longer
        a = ChannelUnsubscribe(**data)
        return a


if __name__ == '__main__':
    import doctest
    doctest.testmod()
