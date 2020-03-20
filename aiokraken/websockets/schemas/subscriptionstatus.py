
from dataclasses import dataclass

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
    channel_id = fields.Integer(data_key="channelID")
    channel_name = fields.String(data_key="channelName")
    event = fields.Constant("subscriptionStatus")
    pair = fields.String()
    status = fields.String()  #TODO : enum ?
    subscription = fields.Nested(SubscriptionSchema())

    @post_load
    def build_model(self, data, **kwargs):
        data.pop('event')  # not needed any longer
        a = SubscriptionStatus(**data)
        return a


# def subscription_expect() -> SubscriptionStatusSchema:
#
#     ExpectedSchema = SubscriptionStatusSchema
#     ExceptedSchema.pair = fields.Constant
#     re
#
