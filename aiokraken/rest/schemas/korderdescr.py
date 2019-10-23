import typing
from decimal import Decimal

from enum import (IntEnum)
from dataclasses import dataclass, field, asdict

from marshmallow import fields, post_load, pre_dump, post_dump
from hypothesis import strategies as st

if not __package__:
    __package__ = 'aiokraken.rest.schemas'

from .base import BaseSchema
from .kpair import PairModel, PairField, PairStrategy
from .ktype import KTypeModel, KTypeField, KTypeStrategy
from .kordertype import KOrderTypeModel, KOrderTypeField, KOrderTypeStrategy
from ...utils.stringenum import StringEnum


@dataclass(init=False, repr=False)
class KOrderDescrModel:
    pair: PairModel
    type: KTypeModel
    ordertype: KOrderTypeModel
    order: str
    price: typing.Optional[Decimal]
    price2: typing.Optional[Decimal]
    leverage: Decimal  # TODO
    close: typing.Optional[str]  # TODO

    def __init__(self, pair: PairModel, type: KTypeModel, ordertype: KOrderTypeModel, price:typing.Optional[Decimal]=None, price2:typing.Optional[Decimal]=None, leverage:Decimal=Decimal(0), close=None, order:str=''):
        """
        Initializes a Order Description.
        price and price2 are optional. consistency with ordertype is handled in code here.
        :param pair: The pair for this order
        :param type: the direction of order (buy/sell)
        :param ordertype: the type of order (market, limit, stoploss, etc.)
        :param price: the price (depends on ordertype - see API doc)
        :param price2: the price2 (depends on ordertype - see API doc)
        :param leverage: the leverage
        :param close: the close order related to this one
        """
        self.pair = pair
        self.type = type
        self.ordertype = ordertype

        #     limit (price = limit price)
        #     stop-loss (price = stop loss price)
        #     take-profit (price = take profit price)
        #     stop-loss-profit (price = stop loss price, price2 = take profit price)
        #     stop-loss-profit-limit (price = stop loss price, price2 = take profit price)
        #     stop-loss-limit (price = stop loss trigger price, price2 = triggered limit price)
        #     take-profit-limit (price = take profit trigger price, price2 = triggered limit price)
        #     trailing-stop (price = trailing stop offset)
        #     trailing-stop-limit (price = trailing stop offset, price2 = triggered limit offset)
        #     stop-loss-and-limit (price = stop loss price, price2 = limit price)

        self.price = price
        self.price2 = price2

        # enforcing consistency as early as possible
        if self.ordertype == KOrderTypeModel.market:
            assert price is None, print(f"price: {price} with {self.ordertype}")
            assert price2 is None, print(f"price2: {price2} with {self.ordertype}")
        elif self.ordertype in [KOrderTypeModel.limit, KOrderTypeModel.stop_loss, KOrderTypeModel.take_profit, KOrderTypeModel.trailing_stop]:
            assert price is not None, print(f"price: {price} with {self.ordertype}")
            assert price2 is None, print(f"price2: {price2} with {self.ordertype}")
        elif self.ordertype in [KOrderTypeModel.stop_loss_profit, KOrderTypeModel.stop_loss_profit_limit, KOrderTypeModel.stop_loss_limit, KOrderTypeModel.take_profit_limit, KOrderTypeModel.trailing_stop_limit, KOrderTypeModel.stop_loss_and_limit]:
            assert price is not None, print(f"price: {price} with {self.ordertype}")
            assert price2 is not None, print(f"price2: {price2} with {self.ordertype}")

        self.leverage = leverage
        self.close = close

        self.order = order or f"{self.type} @ {self.price} {self.ordertype}"  # TODO : match that onto kraken returned order descr

    def __repr__(self):
        return self.order


@st.composite
def KOrderDescrStrategy(draw,
        pair=PairStrategy(),
        type=KTypeStrategy(),
        ordertype=KOrderTypeStrategy(),
        order= None,  # can be overriden by caller # TODO :refine this...
        price= None,  # can be overriden by caller
        price2= None,  # can be overriden by caller
        leverage= st.decimals(allow_nan=False, allow_infinity=False),  # TODO
        close= st.one_of(st.text(max_size=5), st.none()),  # TODO
):
    # Logic to get correct assignement (as per API documentation)  of price and price2
    if order is None:
        order = st.none()  # same logic as for price : None === st.none() generator...
    ot = draw(ordertype)
    if ot in [KOrderTypeModel.limit, KOrderTypeModel.stop_loss, KOrderTypeModel.take_profit,
                            KOrderTypeModel.trailing_stop]:
        if price is None:
            price =st.decimals(allow_nan=False, allow_infinity=False)
        if price2 is None:
            price2 = st.none()
    elif ot in [KOrderTypeModel.stop_loss_profit, KOrderTypeModel.stop_loss_profit_limit,
                            KOrderTypeModel.stop_loss_limit, KOrderTypeModel.take_profit_limit,
                            KOrderTypeModel.trailing_stop_limit, KOrderTypeModel.stop_loss_and_limit]:
        if price is None:
            price = st.decimals(allow_nan=False, allow_infinity=False)
        if price2 is None:
            price2 = st.decimals(allow_nan=False, allow_infinity=False)

    else:  # market or forgotten enum value...
        if price is None:
            price = st.none()
        if price2 is None:
            price2 = st.none()

    return KOrderDescrModel(pair=draw(pair),
                            type =draw(type),
                            ordertype=ot,
                            order=draw(order),
                            price=draw(price),
                            price2=draw(price2),
                            leverage=draw(leverage),
                            close=draw(close))


class KOrderDescrSchema(BaseSchema):
    pair = PairField()
    type = KTypeField()
    ordertype = KOrderTypeField()
    price = fields.Decimal(required=False, as_string=True)
    price2 = fields.Decimal(required=False, as_string=True)
    leverage = fields.Decimal(required=False, as_string=True)  # ???
    order = fields.Str()
    close = fields.Str(required=False)  # ???

    @post_load
    def build_model(self, data, **kwargs):
        return KOrderDescrModel(**data)

    @post_dump
    def filter_dict(self, data, **kwargs):
        data = {k: v for k, v in data.items() if v is not None}
        return data

@st.composite
def KOrderDescrDictStrategy(draw,
                            # Here we mirror arguments for the model strategy
                            pair=PairStrategy(),
                            type=KTypeStrategy(),
                            ordertype=KOrderTypeStrategy(),
                            order= None,  # TODO :refine this...
                            price=None,
                            price2=None,
                            leverage= st.decimals(allow_nan=False, allow_infinity=False),  # TODO
                            close= st.one_of(st.text(max_size=5), st.none()),  # TODO
                            ):
    model = draw(KOrderDescrStrategy(pair=pair, type = type, ordertype=ordertype, order=order, price=price, price2=price2, leverage=leverage, close=close))
    schema = KOrderDescrSchema()
    return schema.dump(model)


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
