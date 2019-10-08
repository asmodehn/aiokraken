import marshmallow
from marshmallow import fields, pre_load, post_load

from .base import BaseSchema

from ..exceptions import AIOKrakenException
from ...model.order import Order, MarketOrder, LimitOrder


class OrderSchema(BaseSchema):

    """ Schema to produce dict from model"""

    pair = fields.Str(required=True)
    volume = fields.Number(required=True)
    leverage = fields.Str()

    starttm = fields.Str()
    expiretm = fields.Str()

    oflags = fields.List(fields.Str())

    validate = fields.Bool()
    userref = fields.List(fields.Str())

    close = fields.Str()

    price = fields.Str()
    price2 = fields.Str()

