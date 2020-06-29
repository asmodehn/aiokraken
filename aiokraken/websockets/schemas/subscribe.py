from dataclasses import dataclass, field

import typing

from marshmallow import fields, post_load, post_dump, pre_load, pre_dump

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class Subscription:
    name: str  # TODO : maybe change into enum ??
    interval: typing.Optional[int] = field(default=None)  # needs ot be empty sometimes (fi ticker)
    depth: typing.Optional[int] = field(default=None)  # needs ot be empty sometimes (fi ticker)
    token: typing.Optional[str] = field(default=None)  # for private data endpoints only, empty otherwise


@dataclass(frozen=True)
class SubscribeOne:
    subscription: Subscription
    pair: str
    # TODO : use pair with proper type

    # not part of hash or equality (for equality between two Subscribe instance/requests)
    reqid: typing.Optional[int] = field(default=None, compare=False)  # reqid does not matter in subscribe requests.


@dataclass(frozen=True)
class Subscribe:
    subscription: Subscription
    pair: typing.FrozenSet[str]
    # TODO : use pair with proper type

    # not part of hash or equality (for equality between two Subscribe instance/requests)
    reqid: typing.Optional[int] = field(default=None, hash=False)

    # need an __init__ here to transform an iterable (pairs) into a frozenset for hashing as a dict key
    def __init__(self, subscription, pair: typing.Optional[typing.Iterable] = None, reqid = None):
        object.__setattr__(self, "subscription", subscription)
        object.__setattr__(self, "pair", frozenset(pair) if pair is not None else frozenset())
        object.__setattr__(self, "reqid", reqid)

    def __contains__(self, item: SubscribeOne):
        return item.reqid == self.reqid and item.subscription == self.subscription and item.pair in self.pair

    def __iter__(self):
        return (SubscribeOne(subscription=self.subscription, pair=p, reqid=self.reqid) for p in self.pair)

    # TODO : do we really need both ? probably not...

    def __getitem__(self, item):
        if item not in self.pair:
            raise KeyError(item)
        return SubscribeOne(subscription=self.subscription, pair=item, reqid=self.reqid)

    def __len__(self):
        return len(self.pair)


class SubscriptionSchema(BaseSchema):
    """
    >>> s= SubscriptionSchema()
    >>> s.load({
    ... 'name': 'ticker',
    ... })
    Subscription(name='ticker', interval=None, depth=None, token='')
    """
    name = fields.String()
    depth = fields.Integer()
    interval = fields.Integer()
    token = fields.String()  # Maybe optional and model defaults to none ?

    @post_load
    def build_model(self, data, **kwargs):
        a = Subscription(**data)
        return a

    @post_dump
    def drop_Nones(self, data, **kwargs):
        return {k: v for k, v in data.items() if v is not None}


class SubscribeSchema(BaseSchema):
    """
    >>> s= SubscribeSchema()
    >>> s.load({'event': 'subscribe',
    ... 'pair': ['XBT/USD'],
    ... 'subscription': {'name': 'ticker'}
    ... })
    Subscribe(subscription=Subscription(name='ticker', interval=None, depth=None, token=''), pair=['XBT/USD'], reqid=None)
    """
    event = fields.Constant("subscribe")
    pair = fields.List(fields.String())
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
