
from dataclasses import dataclass, field

import typing

from aiokraken.websockets.schemas.subscribe import Subscription, SubscriptionSchema
from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class SubscriptionStatus:
    channel_id: int
    channel_name: str
    pair: str
    status: str
    subscription: Subscription

    # not part of hash or equality (for equality between two Subscribe instance/requests)
    reqid: typing.Optional[int] = field(default=None, hash=False)


@dataclass(frozen=True)
class SubscriptionStatusError:
    status: str
    error_message: str


class SubscriptionStatusSchema(BaseSchema):
    """
    >>> s= SubscriptionStatusSchema()
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
    channel_id = fields.Integer(data_key="channelID")
    error_message = fields.String(data_key="errorMessage", required=False)
    # we model error message as being optional on schema but changing datatype upon instantiation.

    channel_name = fields.String(data_key="channelName")
    event = fields.Constant("subscriptionStatus")
    pair = fields.String()
    status = fields.String()  # TODO : enum ? don't forget error.
    subscription = fields.Nested(SubscriptionSchema())

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # not needed any longer

        if data['status'] == 'error':
            a = SubscriptionStatusError(**data)
        else:
            a = SubscriptionStatus(**data)
        return a


# def subscription_expect() -> SubscriptionStatusSchema:
#
#     ExpectedSchema = SubscriptionStatusSchema
#     ExceptedSchema.pair = fields.Constant
#     re
#
