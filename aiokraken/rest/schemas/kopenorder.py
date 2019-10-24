import typing
from decimal import Decimal

from enum import (IntEnum)
from dataclasses import dataclass, field

from hypothesis._strategies import composite
from marshmallow import fields, post_load
from hypothesis import strategies as st

if not __package__:
    __package__ = 'aiokraken.rest.schemas'

from .base import BaseSchema
from .kpair import PairModel, PairField
from .ktype import KABTypeModel, KABTypeField
from .kordertype import KOrderTypeModel, KOrderTypeField
from .ktm import TMModel, TMStrategy, TimerField
from .korderdescr import KOrderDescrModel, KOrderDescrSchema, KOrderDescrStrategy
from ...utils.stringenum import StringEnum


@dataclass(frozen=True)
class KOpenOrderModel:
    descr: KOrderDescrModel

    status: str  # TODO
    starttm: TMModel
    opentm: TMModel
    expiretm: TMModel

    price: Decimal
    limitprice: Decimal
    stopprice: Decimal

    vol: Decimal
    vol_exec: Decimal

    fee: Decimal
    cost: Decimal

    misc: str  # TODO
    oflags: str  # TODO

    refid: int  # TODO
    userref: int  # TODO


    # def filled(self):
    #
    #     return Trade

@composite
def OpenOrderStrategy(draw,
                      descr= KOrderDescrStrategy(),
                      status= st.text(max_size=5),  # TODO
                      starttm= TMStrategy(),
                      opentm= TMStrategy(),
                      expiretm= TMStrategy(),

                      price= st.decimals(allow_nan=False, allow_infinity=False),
                      limitprice= st.decimals(allow_nan=False, allow_infinity=False),
                      stopprice= st.decimals(allow_nan=False, allow_infinity=False),

                      vol= st.decimals(allow_nan=False, allow_infinity=False),
                      vol_exec= st.decimals(allow_nan=False, allow_infinity=False),

                      fee= st.decimals(allow_nan=False, allow_infinity=False),
                      cost= st.decimals(allow_nan=False, allow_infinity=False),

                      misc= st.text(max_size=5),  # TODO
                      oflags= st.text(max_size=5), # TODO

                      refid=st.integers(),  # TODO
                      userref= st.integers() # TODO
):

    return KOpenOrderModel(
        descr = draw(descr),
        status = draw(status),
        starttm= draw(starttm),
        opentm  =draw(opentm),
        expiretm= draw(expiretm),

        price= draw(price),
        limitprice=draw(limitprice),
        stopprice=draw(stopprice),

        vol=draw(vol),
        vol_exec=draw(vol_exec),

        fee= draw(fee),
        cost= draw(cost),

        misc=draw(misc),
        oflags=draw(oflags),

        refid=draw(refid),
        userref=draw(userref)
    )


class KOpenOrderSchema(BaseSchema):
    refid = fields.Integer(allow_none=True)
    userref = fields.Integer()
    status = fields.Str()
        # pending = order pending book entry
        # open = open order
        # closed = closed order
        # canceled = order canceled
        # expired = order expired
    opentm = TimerField()
    starttm = TimerField()
    expiretm = TimerField()
    descr = fields.Nested(KOrderDescrSchema())
    vol = fields.Decimal(as_string=True)  #(base currency unless viqc set in oflags)
    vol_exec = fields.Decimal(as_string=True) #(base currency unless viqc set in oflags)
    cost = fields.Decimal(as_string=True)  #(quote currency unless unless viqc set in oflags)
    fee = fields.Decimal(as_string=True) #(quote currency)
    price = fields.Decimal(as_string=True)  #(quote currency unless viqc set in oflags)
    stopprice = fields.Decimal(as_string=True)  #(quote currency, for trailing stops)
    limitprice = fields.Decimal(as_string=True)  #(quote currency, when limit based order type triggered)
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
    trades = fields.List(fields.Number())  #array of trade ids related to order

    @post_load
    def build_model(self, data, **kwargs):
        return KOpenOrderModel(**data)



@st.composite
def OpenOrderDictStrategy(draw,
                          # Here we mirror arguments for the model strategy
                          descr= KOrderDescrStrategy(),
                          status= st.text(max_size=5),  # TODO
                          starttm= TMStrategy(),
                          opentm= TMStrategy(),
                          expiretm= TMStrategy(),

                          price= st.decimals(allow_nan=False, allow_infinity=False),
                          limitprice= st.decimals(allow_nan=False, allow_infinity=False),
                          stopprice= st.decimals(allow_nan=False, allow_infinity=False),

                          vol= st.decimals(allow_nan=False, allow_infinity=False),
                          vol_exec= st.decimals(allow_nan=False, allow_infinity=False),

                          fee= st.decimals(allow_nan=False, allow_infinity=False),
                          cost= st.decimals(allow_nan=False, allow_infinity=False),

                          misc= st.text(max_size=5),  # TODO
                          oflags= st.text(max_size=5),  # TODO

                          refid=st.integers(),  # TODO
                          userref= st.integers()  # TODO
                          ):
    model = draw(OpenOrderStrategy(descr= descr,
                      status= status,
                      starttm= starttm,
                      opentm= opentm,
                      expiretm= expiretm,

                      price= price,
                      limitprice= limitprice,
                      stopprice= stopprice,

                      vol= vol,
                      vol_exec= vol_exec,

                      fee= fee,
                      cost= cost,

                      misc= misc,  # TODO
                      oflags= oflags, # TODO

                      refid=refid,  # TODO
                      userref= userref  # TODO
    ))
    schema = KOpenOrderSchema()
    return schema.dump(model)


class OpenOrdersResponseSchema(BaseSchema):
    open = fields.Dict(keys=fields.Str(), values=fields.Nested(KOpenOrderSchema()))

    @post_load
    def build_model(self, data, **kwargs):
        return data['open']


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
