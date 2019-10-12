import marshmallow
from marshmallow import fields, pre_load, post_load

from .base import BaseSchema

from ..exceptions import AIOKrakenException
from ...model.order import Order, MarketOrder, LimitOrder


class OrderSchema(BaseSchema):

    """ Schema to produce dict from model"""

    type = fields.Str(required=True)
    ordertype = fields.Str(required=True)

    pair = fields.Str(required=True)
    volume = fields.Number(required=True)
    leverage = fields.Str()

    starttm = fields.Str()
    expiretm = fields.Str()

    oflags = fields.List(fields.Str())

    validate = fields.Bool()
    userref = fields.Int()  # 32 bits signed number  # Ref : https://www.kraken.com/features/api#private-user-trading

    close = fields.Str()

    price = fields.Decimal(places=1, as_string=True)  # TODO : number of places likely depend on currency pair ?? 1 for BTC/EUR
    price2 = fields.Decimal(places=1, as_string=True)


class OrderDescriptionSchema(BaseSchema):
    order = fields.Str(required=True)  # order description
    close = fields.Str()  # conditional close order description (if conditional close set)


class AddOrderResponseSchema(BaseSchema):
    descr = fields.Nested(OrderDescriptionSchema)
    txid = fields.Integer(many=True)  #array of transaction ids for order (if order was added successfully)


class CancelOrderResponseSchema(BaseSchema):
    pending = fields.List(fields.Str())
    count = fields.Integer()  #array of transaction ids for order (if order was added successfully)


class OrderInfoSchema(BaseSchema):
    pair = fields.Str()
    type = fields.Str()  #(buy/sell)
    ordertype = fields.Str()  #(See Add standard order)
    price =fields.Number()
    price2 = fields.Number()
    leverage = fields.Number()
    order = fields.Str()
    close = fields.Str()


class OpenOrderSchema(BaseSchema):
    refid = fields.Integer()
    userref = fields.Integer()
    status = fields.Str()
        # pending = order pending book entry
        # open = open order
        # closed = closed order
        # canceled = order canceled
        # expired = order expired
    opentm = fields.Str()
    starttm = fields.Str()
    expiretm = fields.Str()
    descr = fields.Nested(OrderInfoSchema)
    vol = fields.Number()  #(base currency unless viqc set in oflags)
    vol_exec = fields.Number() #(base currency unless viqc set in oflags)
    cost = fields.Number()  #(quote currency unless unless viqc set in oflags)
    fee = fields.Number() #(quote currency)
    price = fields.Number()  #(quote currency unless viqc set in oflags)
    stopprice = fields.Number()  #(quote currency, for trailing stops)
    limitprice = fields.Number()  #(quote currency, when limit based order type triggered)
    misc = fields.Str()  #comma delimited list of miscellaneous info
        # stopped = triggered by stop price
        # touched = triggered by touch price
        # liquidated = liquidation
        # partial = partial fill
    oflags = fields.Str() #comma delimited list of order flags
        # viqc = volume in quote currency
        # fcib = prefer fee in base currency (default if selling)
        # fciq = prefer fee in quote currency (default if buying)
        # nompp = no market price protection
    trades = fields.List(fields.Number)  #array of trade ids related to order


class OpenOrdersResponseSchema(BaseSchema):
    open = fields.Nested(OpenOrderSchema)
