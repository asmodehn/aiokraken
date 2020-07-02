
from dataclasses import dataclass, field

import typing

from aiokraken.websockets.schemas.subscribe import Subscription, SubscriptionSchema
from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class PrivateSubscriptionStatus:
    channel_name: str
    status: str
    subscription: Subscription

    # not part of hash or equality (for equality between two Subscribe instance/requests)
    reqid: typing.Optional[int] = field(default=None, hash=False)


@dataclass(frozen=True)
class PublicSubscriptionStatus:
    channel_name: str
    status: str
    subscription: Subscription

    pair: str
    channel_id: int

    # not part of hash or equality (for equality between two Subscribe instance/requests)
    reqid: typing.Optional[int] = field(default=None, hash=False)


@dataclass(frozen=True)
class SubscriptionStatusError:
    status: str
    error_message: str


class PrivateSubscriptionStatusSchema(BaseSchema):
    """
    >>> s= PrivateSubscriptionStatusSchema()
    >>> s.load({'channelName': 'ticker',
    ... 'event': 'subscriptionStatus',
    ... 'status': 'subscribed',
    ... 'subscription': {'name': 'ownTrades'}
    ... })
    KAsset(altname='ALTNAME', aclass='ACLASS', decimals=42, display_decimals=7)
    """

    error_message = fields.String(data_key="errorMessage", required=False)
    # we model error message as being optional on schema but changing datatype upon instantiation.

    channel_name = fields.String(data_key="channelName")
    event = fields.Constant("subscriptionStatus")

    status = fields.String()  # TODO : enum ? don't forget error.
    subscription = fields.Nested(SubscriptionSchema())

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # not needed any longer

        if data['status'] == 'error':
            a = SubscriptionStatusError(**data)
        else:
            a = PrivateSubscriptionStatus(**data)
        return a


class PublicSubscriptionStatusSchema(BaseSchema):
    """
    >>> s= PublicSubscriptionStatusSchema()
    >>> s.load({'channelID': 229,
    ... 'channelName': 'ticker',
    ... 'event': 'subscriptionStatus',
    ... 'pair': 'XBT/USD',
    ... 'status': 'subscribed',
    ... 'subscription': {'name': 'ticker'}
    ... })
    KAsset(altname='ALTNAME', aclass='ACLASS', decimals=42, display_decimals=7)
    """
    # one of these
    channel_id = fields.Integer(data_key="channelID", required=False)
    # Note : channel_id might not be there (seems to be present only when list of pair is accepted on subscribe...)

    error_message = fields.String(data_key="errorMessage", required=False)
    # we model error message as being optional on schema but changing datatype upon instantiation.

    channel_name = fields.String(data_key="channelName")
    event = fields.Constant("subscriptionStatus")
    pair = fields.String(required=False)  # Note : this might not be there (not all endpoints require a pair)
    status = fields.String()  # TODO : enum ? don't forget error.
    subscription = fields.Nested(SubscriptionSchema())

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # not needed any longer

        if data['status'] == 'error':
            a = SubscriptionStatusError(**data)
        else:
            a = PublicSubscriptionStatus(**data)
        return a

# def subscription_expect() -> SubscriptionStatusSchema:
#
#     ExpectedSchema = SubscriptionStatusSchema
#     ExceptedSchema.pair = fields.Constant
#     re
#
