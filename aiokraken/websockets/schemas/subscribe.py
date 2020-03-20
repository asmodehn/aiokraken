from dataclasses import dataclass, field

import typing

from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class Subscription:
    name: str  # TODO : maybe change into enum ??
    depth: typing.Optional[int] = field(default=10)
    interval: typing.Optional[int] = field(default=1)
    token: typing.Optional[str] = field(default="")  # for private data endpoints only


@dataclass(frozen=True)
class Subscribe:
    subscription: Subscription
    pair: typing.List[str]  # TODO : use pair with proper type
    reqid: typing.Optional[int] = field(default=None)


class SubscriptionSchema(BaseSchema):
    """
    >>> s= SubscriptionSchema()
    >>> s.load({
    ... 'name': 'ticker',
    ... })
    Subscription(name='ticker', depth=10, interval=1, token='')
    """
    name = fields.String()
    depth = fields.Integer()
    interval = fields.Integer()
    token = fields.String()

    @post_load
    def build_model(self, data, **kwargs):
        a = Subscription(**data)
        return a


class SubscribeSchema(BaseSchema):
    """
    >>> s= SubscribeSchema()
    >>> s.load({'event': 'subscription',
    ... 'pair': 'XBT/USD',
    ... 'subscription': {'name': 'ticker'}
    ... })
    Subscribe(subscription=Subscription(name='ticker', depth=10, interval=1, token=''), pair='XBT/USD', reqid=None)
    """
    event = fields.Constant("subscribe")
    pair = fields.String()
    status = fields.String()
    subscription = fields.Nested(SubscriptionSchema())

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # not needed any longer
        a = Subscribe(**data)
        return a


if __name__ == '__main__':
    import doctest
    doctest.testmod()
