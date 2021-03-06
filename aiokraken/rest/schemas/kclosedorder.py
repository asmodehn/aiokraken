import typing
from datetime import datetime
from decimal import Decimal

from enum import (IntEnum)
from dataclasses import dataclass, field

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
from .kopenorder import KOpenOrderModel, KOpenOrderSchema

@dataclass(frozen=True)
class KClosedOrderModel(KOpenOrderModel):
    # Note :
    # refid likely None
    # userref likely None
    closetm: datetime = None  # this must have a default because base class has defaults...
    reason: typing.Optional[str] = None  # Note : might be None # TODO : fix this defaults thing somehow...


@st.composite
def ClosedOrderStrategy(draw,

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

                      refid=st.one_of(st.none(),st.integers()),  # TODO
                      userref= st.one_of(st.none(),st.integers()),  # TODO

                        trades=st.lists(st.text(max_size=5), max_size=5),

                        closetm=AbsoluteTimeStrategy(),
                        reason=st.one_of(st.none(), st.text(max_size=5))

):

    return KClosedOrderModel(
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

        closetm=draw(closetm),
        reason=draw(reason)
    )


class KClosedOrderSchema(KOpenOrderSchema):

    closetm = TimerField()  # unix timestamp of when order was closed
    reason = fields.Str(allow_none=True, required=False)  # additional info on status (if any)

    @post_load
    def build_model(self, data, **kwargs):
        return KClosedOrderModel(**data)


@st.composite
def ClosedOrderDictStrategy(draw,
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

                            trades=st.lists(st.text(max_size=5), max_size=5),

                            closetm= AbsoluteTimeStrategy(),
                            reason=st.one_of(st.none(), st.text(max_size=5))
                          ):
    model = draw(ClosedOrderStrategy(descr= descr,
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

                        closetm= closetm,
                        reason=reason
    ))
    schema = KClosedOrderSchema()
    return schema.dump(model)


class ClosedOrdersResponseSchema(BaseSchema):
    closed = fields.Dict(keys=fields.Str(), values=fields.Nested(KClosedOrderSchema()))
    count = fields.Integer()  # amount of available order info matching criteria

    @post_load
    def build_model(self, data, **kwargs):
        return data['closed'], data['count']



# closed = array of order info.  See Get open orders.  Additional fields:
#     closetm = unix timestamp of when order was closed
#     reason = additional info on status (if any)
# count = amount of available order info matching criteria

if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
