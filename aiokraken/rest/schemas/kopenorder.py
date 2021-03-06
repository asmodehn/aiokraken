import typing
from datetime import datetime
from decimal import Decimal

from enum import (IntEnum)
from dataclasses import dataclass, field

from hypothesis.strategies import composite
from marshmallow import fields, post_load
from hypothesis import strategies as st

if not __package__:
    __package__ = 'aiokraken.rest.schemas'

from .base import BaseSchema
from .kordertype import KOrderTypeModel, KOrderTypeField
from .ktm import AbsoluteTimeStrategy, TimerField
from .korderdescr import (KOrderDescrNoPriceFinalized,
           KOrderDescrOnePriceFinalized,
           KOrderDescrTwoPriceFinalized,
                          KOrderDescrNoPriceStrategy,
                          KOrderDescrOnePriceStrategy,
                          KOrderDescrTwoPriceStrategy,
                    KOrderDescrFinalizeStrategy,

KOrderDescrSchema,
)

@dataclass(frozen=True)
class KOpenOrderModel:
    descr: typing.Union[KOrderDescrNoPriceFinalized,
           KOrderDescrOnePriceFinalized,
           KOrderDescrTwoPriceFinalized, ]

    status: str  # TODO
    starttm: datetime
    opentm: datetime
    expiretm: datetime

    price: Decimal
    limitprice: Decimal
    stopprice: Decimal

    vol: Decimal
    vol_exec: Decimal

    fee: Decimal
    cost: Decimal

    misc: str  # TODO
    oflags: str  # TODO

    refid: typing.Optional[int] = None  # TODO
    userref: typing.Optional[int] = None  # TODO

    trades: typing.Optional[typing.List[str]] = None


@composite
def OpenOrderStrategy(draw,
                      descr= st.one_of([
                          KOrderDescrFinalizeStrategy(strategy=KOrderDescrNoPriceStrategy()),
                          KOrderDescrFinalizeStrategy(strategy=KOrderDescrOnePriceStrategy()),
                          KOrderDescrFinalizeStrategy(strategy=KOrderDescrTwoPriceStrategy())
                      ]),
                      status= st.text(max_size=5),  # TODO
                      starttm= AbsoluteTimeStrategy(),
                      opentm= AbsoluteTimeStrategy(),
                      expiretm= AbsoluteTimeStrategy(),
                      # CAreful here : consistency with descr content ???
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
                      userref= st.integers(),  # TODO

                      trades= st.lists(st.text(max_size=5),max_size=5)
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
        userref=draw(userref),

        trades=draw(trades),
    )


class KOpenOrderSchema(BaseSchema):
    refid = fields.Integer(allow_none=True)
    userref = fields.Integer(allow_none=True)
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
    trades = fields.List(fields.Str(), required=False)  #array of trade ids related to order

    @post_load
    def build_model(self, data, **kwargs):
        return KOpenOrderModel(**data)



@st.composite
def OpenOrderDictStrategy(draw,
                          # Here we mirror arguments for the model strategy
                          descr= st.one_of([
                              KOrderDescrFinalizeStrategy(strategy=KOrderDescrNoPriceStrategy()),
                              KOrderDescrFinalizeStrategy(strategy=KOrderDescrOnePriceStrategy()),
                              KOrderDescrFinalizeStrategy(strategy=KOrderDescrTwoPriceStrategy())
                          ]),
                          status= st.text(max_size=5),  # TODO
                          starttm= AbsoluteTimeStrategy(),
                          opentm= AbsoluteTimeStrategy(),
                          expiretm= AbsoluteTimeStrategy(),

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
                          userref= st.integers(),  # TODO

                            trades= st.lists(st.text(max_size=5),max_size=5),
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
                      userref= userref,  # TODO

                    trades=trades,
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
