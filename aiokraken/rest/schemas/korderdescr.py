from __future__ import annotations
import functools
import typing
from decimal import Decimal

from enum import IntEnum
from dataclasses import dataclass, field, asdict

from marshmallow import fields, post_load, pre_dump, post_dump, pre_load
from hypothesis import strategies as st

if not __package__:
    __package__ = "aiokraken.rest.schemas"

from .base import BaseSchema
from .kpair import PairModel, PairField, PairStrategy
from .kabtype import KABTypeModel, KABTypeField, KABTypeStrategy
from .kordertype import KOrderTypeModel, KOrderTypeField, KOrderTypeStrategy

# TODO : repr for dataclasses ! (should be isomorphic to order string representation frmo kraken)

# This multilevel inheritance is for enforcing sequential call, building data bit by bit, and verifiable via types...
# Difficulty : we need 2 orthogonal dimensions... attempting with python's multiple inheritance...
@dataclass(frozen=True, init=False)
class KOrderDescrMixin:
    pair: PairModel  # always needed, usually from context

    def __init__(self, pair: PairModel, **kwargs):
        object.__setattr__(self, "pair", pair)
        super(KOrderDescrMixin, self).__init__(**kwargs)


# TODO : we need to overload init there to allow multiple inheritance and work with constructors...
#  => better way ? enhancement in python dataclasses ??


@dataclass(frozen=True, init=False)
class KOrderDescrNoPriceMixin(KOrderDescrMixin):
    ordertype: KOrderTypeModel

    def __init__(self, ordertype: KOrderTypeModel, **kwargs):
        object.__setattr__(self, "ordertype", ordertype)
        super(KOrderDescrNoPriceMixin, self).__init__(**kwargs)


@dataclass(frozen=True, init=False)
class KOrderDescrOnePriceMixin(KOrderDescrMixin):
    ordertype: KOrderTypeModel
    price: Decimal

    def __init__(self, ordertype: KOrderTypeModel, price: Decimal, **kwargs):
        object.__setattr__(self, "ordertype", ordertype)
        object.__setattr__(self, "price", price)
        super(KOrderDescrOnePriceMixin, self).__init__(**kwargs)


@dataclass(frozen=True, init=False)
class KOrderDescrTwoPriceMixin(KOrderDescrMixin):
    ordertype: KOrderTypeModel
    price: Decimal
    price2: Decimal

    def __init__(
        self, ordertype: KOrderTypeModel, price: Decimal, price2: Decimal, **kwargs
    ):
        object.__setattr__(self, "ordertype", ordertype)
        object.__setattr__(self, "price", price)
        object.__setattr__(self, "price2", price2)
        super(KOrderDescrTwoPriceMixin, self).__init__(**kwargs)


@dataclass(frozen=True, init=False)
class KOrderDescrFinalizedMixin:
    abtype: KABTypeModel
    leverage: Decimal
    close: typing.Optional[
        typing.Union[
            KOrderDescrNoPriceMixin, KOrderDescrOnePriceMixin, KOrderDescrTwoPriceMixin
        ]
    ]

    def __init__(
        self,
        abtype: KABTypeModel,
        leverage: Decimal = Decimal(0),
        close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceMixin,
                KOrderDescrOnePriceMixin,
                KOrderDescrTwoPriceMixin,
            ]
        ] = None,
        **kwargs
    ):
        object.__setattr__(self, "abtype", abtype)
        object.__setattr__(self, "leverage", leverage)
        object.__setattr__(self, "close", close)
        super(KOrderDescrFinalizedMixin, self).__init__(**kwargs)


# categorical product via multi inheritance (careful with MRO)...

# Terminal
class KOrderDescrNoPriceFinalized(KOrderDescrNoPriceMixin, KOrderDescrFinalizedMixin):
    pass


class KOrderDescrOnePriceFinalized(KOrderDescrOnePriceMixin, KOrderDescrFinalizedMixin):
    pass


class KOrderDescrTwoPriceFinalized(KOrderDescrTwoPriceMixin, KOrderDescrFinalizedMixin):
    pass


class KOrderDescrNoPrice(KOrderDescrNoPriceMixin, KOrderDescrMixin):
    def buy(
        self,
        leverage,
        close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceMixin,
                KOrderDescrOnePriceMixin,
                KOrderDescrTwoPriceMixin,
            ]
        ] = None,
    ) -> KOrderDescrNoPriceFinalized:
        return KOrderDescrNoPriceFinalized(
            pair=self.pair,
            ordertype=self.ordertype,
            abtype=KABTypeModel.buy,
            leverage=leverage,
            close=close,
        )

    def sell(
        self,
        leverage,
        close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceMixin,
                KOrderDescrOnePriceMixin,
                KOrderDescrTwoPriceMixin,
            ]
        ] = None,
    ) -> KOrderDescrNoPriceFinalized:
        return KOrderDescrNoPriceFinalized(
            pair=self.pair,
            ordertype=self.ordertype,
            abtype=KABTypeModel.sell,
            leverage=leverage,
            close=close,
        )


class KOrderDescrOnePrice(KOrderDescrOnePriceMixin, KOrderDescrMixin):
    def buy(
        self,
        leverage,
        close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceMixin,
                KOrderDescrOnePriceMixin,
                KOrderDescrTwoPriceMixin,
            ]
        ] = None,
    ) -> KOrderDescrOnePriceFinalized:
        return KOrderDescrOnePriceFinalized(
            pair=self.pair,
            ordertype=self.ordertype,
            price=self.price,
            abtype=KABTypeModel.buy,
            leverage=leverage,
            close=close,
        )

    def sell(
        self,
        leverage,
        close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceMixin,
                KOrderDescrOnePriceMixin,
                KOrderDescrTwoPriceMixin,
            ]
        ] = None,
    ) -> KOrderDescrOnePriceFinalized:
        return KOrderDescrOnePriceFinalized(
            pair=self.pair,
            ordertype=self.ordertype,
            price=self.price,
            abtype=KABTypeModel.sell,
            leverage=leverage,
            close=close,
        )


class KOrderDescrTwoPrice(KOrderDescrTwoPriceMixin, KOrderDescrMixin):
    def buy(
        self,
        leverage,
        close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceMixin,
                KOrderDescrOnePriceMixin,
                KOrderDescrTwoPriceMixin,
            ]
        ] = None,
    ) -> KOrderDescrTwoPriceFinalized:
        return KOrderDescrTwoPriceFinalized(
            pair=self.pair,
            ordertype=self.ordertype,
            price=self.price,
            price2=self.price2,
            abtype=KABTypeModel.buy,
            leverage=leverage,
            close=close,
        )

    def sell(
        self,
        leverage,
        close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceMixin,
                KOrderDescrOnePriceMixin,
                KOrderDescrTwoPriceMixin,
            ]
        ] = None,
    ) -> KOrderDescrTwoPriceFinalized:
        return KOrderDescrTwoPriceFinalized(
            pair=self.pair,
            ordertype=self.ordertype,
            price=self.price,
            price2=self.price2,
            abtype=KABTypeModel.sell,
            leverage=leverage,
            close=close,
        )


# Initial
class KOrderDescr(KOrderDescrMixin):

    # market
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
    #     settle-position

    def market(self) -> KOrderDescrNoPrice:
        return KOrderDescrNoPrice(pair=self.pair, ordertype=KOrderTypeModel.market)

    def limit(self, limit_price: Decimal) -> KOrderDescrOnePrice:
        return KOrderDescrOnePrice(
            pair=self.pair, ordertype=KOrderTypeModel.limit, price=limit_price
        )

    def stop_loss(self, stop_loss_price: Decimal) -> KOrderDescrOnePrice:
        return KOrderDescrOnePrice(
            pair=self.pair, ordertype=KOrderTypeModel.stop_loss, price=stop_loss_price
        )

    def take_profit(self, take_profit_price: Decimal) -> KOrderDescrOnePrice:
        return KOrderDescrOnePrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.take_profit,
            price=take_profit_price,
        )

    def stop_loss_profit(
        self, stop_loss_price: Decimal, take_profit_price: Decimal
    ) -> KOrderDescrTwoPrice:
        return KOrderDescrTwoPrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.stop_loss_profit,
            price=stop_loss_price,
            price2=take_profit_price,
        )

    def stop_loss_profit_limit(
        self, stop_loss_price: Decimal, take_profit_price: Decimal
    ) -> KOrderDescrTwoPrice:
        return KOrderDescrTwoPrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.stop_loss_profit_limit,
            price=stop_loss_price,
            price2=take_profit_price,
        )

    def stop_loss_limit(
        self, stop_loss_trigger_price: Decimal, triggered_limit_price: Decimal
    ) -> KOrderDescrTwoPrice:
        return KOrderDescrTwoPrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.stop_loss_limit,
            price=stop_loss_trigger_price,
            price2=triggered_limit_price,
        )

    def take_profit_limit(
        self, take_profit_trigger_price: Decimal, triggered_limit_price: Decimal
    ) -> KOrderDescrTwoPrice:
        return KOrderDescrTwoPrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.take_profit_limit,
            price=take_profit_trigger_price,
            price2=triggered_limit_price,
        )

    def trailing_stop(self, trailing_stop_offset: Decimal) -> KOrderDescrOnePrice:
        return KOrderDescrOnePrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.trailing_stop,
            price=trailing_stop_offset,
        )

    def trailing_stop_limit(
        self, trailing_stop_offset: Decimal, triggered_limit_offset: Decimal
    ) -> KOrderDescrTwoPrice:
        return KOrderDescrTwoPrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.trailing_stop_limit,
            price=trailing_stop_offset,
            price2=triggered_limit_offset,
        )

    def stop_loss_and_limit(
        self, stop_loss_price: Decimal, limit_price: Decimal
    ) -> KOrderDescrTwoPrice:
        return KOrderDescrTwoPrice(
            pair=self.pair,
            ordertype=KOrderTypeModel.stop_loss_and_limit,
            price=stop_loss_price,
            price2=limit_price,
        )

    def settle_position(self) -> KOrderDescrNoPrice:
        return KOrderDescrNoPrice(
            pair=self.pair, ordertype=KOrderTypeModel.settle_position
        )


# These are meant to be internal classes for safety and prevent mistakes via types.
# But not user interface with meaningful names (methods on RequestOrder have that design)


@st.composite
def KOrderDescrNoPriceStrategy(draw,):
    o = draw(st.builds(KOrderDescr))
    ot = draw(
        st.sampled_from([KOrderTypeModel.market, KOrderTypeModel.settle_position])
    )
    if ot == KOrderTypeModel.market:
        op = o.market()
    elif ot == KOrderTypeModel.settle_position:
        op = o.settle_position()
    else:
        raise NotImplementedError
    return op


@st.composite
def KOrderDescrOnePriceStrategy(
    draw, price=st.decimals(allow_nan=False, allow_infinity=False, min_value=1)
):
    o = draw(st.builds(KOrderDescr))
    ot = draw(
        st.sampled_from(
            [
                KOrderTypeModel.limit,
                KOrderTypeModel.take_profit,
                KOrderTypeModel.stop_loss,
                KOrderTypeModel.trailing_stop,
            ]
        )
    )
    if ot == KOrderTypeModel.limit:
        op = o.limit(limit_price=draw(price))
    elif ot == KOrderTypeModel.take_profit:
        op = o.take_profit(take_profit_price=draw(price))
    elif ot == KOrderTypeModel.stop_loss:
        op = o.stop_loss(stop_loss_price=draw(price))
    elif ot == KOrderTypeModel.trailing_stop:
        op = o.trailing_stop(trailing_stop_offset=draw(price))
    else:
        raise NotImplementedError
    return op


@st.composite
def KOrderDescrTwoPriceStrategy(
    draw,
    price=st.decimals(allow_nan=False, allow_infinity=False, min_value=1),
    price2=st.decimals(allow_nan=False, allow_infinity=False, min_value=1),
):
    o = draw(st.builds(KOrderDescr))
    ot = draw(
        st.sampled_from(
            [
                KOrderTypeModel.stop_loss_profit,
                KOrderTypeModel.stop_loss_profit_limit,
                KOrderTypeModel.stop_loss_limit,
                KOrderTypeModel.take_profit_limit,
                KOrderTypeModel.trailing_stop_limit,
                KOrderTypeModel.stop_loss_and_limit,
            ]
        )
    )
    if ot == KOrderTypeModel.stop_loss_profit:
        op = o.stop_loss_profit(
            stop_loss_price=draw(price), take_profit_price=draw(price2)
        )
    elif ot == KOrderTypeModel.stop_loss_profit_limit:
        op = o.stop_loss_profit_limit(
            stop_loss_price=draw(price), take_profit_price=draw(price2)
        )
    elif ot == KOrderTypeModel.stop_loss_limit:
        op = o.stop_loss_limit(
            stop_loss_trigger_price=draw(price), triggered_limit_price=draw(price2)
        )
    elif ot == KOrderTypeModel.take_profit_limit:
        op = o.take_profit_limit(
            take_profit_trigger_price=draw(price), triggered_limit_price=draw(price2)
        )
    elif ot == KOrderTypeModel.trailing_stop_limit:
        op = o.trailing_stop_limit(
            trailing_stop_offset=draw(price), triggered_limit_offset=draw(price2)
        )
    elif ot == KOrderTypeModel.stop_loss_and_limit:
        op = o.stop_loss_and_limit(
            stop_loss_price=draw(price), limit_price=draw(price2)
        )
    else:
        raise NotImplementedError
    return op


@st.composite
def KOrderDescrFinalizeStrategy(
    draw,
    strategy,  # CAREFUL here ... how about typing strategies ???
    leverage=st.decimals(allow_nan=False, allow_infinity=False, min_value=0),
    close=st.one_of(
        KOrderDescrNoPriceStrategy(),
        KOrderDescrOnePriceStrategy(),
        KOrderDescrTwoPriceStrategy(),
        st.none(),
    ),
):
    op = draw(strategy)
    oab = draw(st.sampled_from([KABTypeModel.buy, KABTypeModel.sell]))

    # optional close order
    c = draw(close)

    if oab == KABTypeModel.buy:
        of = op.buy(leverage=draw(leverage), close=c)
    elif oab == KABTypeModel.sell:
        of = op.sell(leverage=draw(leverage), close=c)
    else:
        raise NotImplementedError

    return of


# IMPORTANT : Only ONE schema for multiple internal classes, because we deal only with one external structure,
# even if we want to be more strict with types internally...


class KOrderDescrCloseSchema(BaseSchema):
    # TODO : extra fields ? redundant or implicit ??
    ordertype = KOrderTypeField()
    price = fields.Decimal(required=False, as_string=True)
    price2 = fields.Decimal(required=False, as_string=True)


class KOrderDescrSchema(BaseSchema):
    pair = PairField()
    abtype = KABTypeField()  # need rename to not confuse python on this...
    ordertype = KOrderTypeField()
    price = fields.Decimal(required=False, as_string=True)
    price2 = fields.Decimal(required=False, as_string=True)
    leverage = fields.Decimal(
        required=False, as_string=True
    )  # Kraken returns 'none' on this (cf cassettes)...
    order = fields.Str()  # TODO ??? idea : should be isomorphic to repr()
    close = fields.Nested(nested=KOrderDescrCloseSchema(), required=False)

    @pre_load
    def filter_dict_onload(self, data, **kwargs):
        # filtering 'type' field
        if data.get("type") is not None:
            data["abtype"] = data.pop("type")
        # filtering None fields
        if data.get("leverage") in ["none", "None"]:
            data.pop("leverage")
        return data

    @post_load
    def build_model(self, data, **kwargs):
        # Choose the correct internal type
        if data.get("ordertype") in [
            KOrderTypeModel.market,
            KOrderTypeModel.settle_position,
        ]:
            model = KOrderDescrNoPrice(pair=data["pair"], ordertype=data["ordertype"])
        elif data.get("ordertype") in [
            KOrderTypeModel.limit,
            KOrderTypeModel.take_profit,
            KOrderTypeModel.stop_loss,
            KOrderTypeModel.trailing_stop,
        ]:
            model = KOrderDescrOnePrice(
                pair=data["pair"], ordertype=data["ordertype"], price=data["price"]
            )
        elif data.get("ordertype") in [
            KOrderTypeModel.stop_loss_profit,
            KOrderTypeModel.stop_loss_profit_limit,
            KOrderTypeModel.stop_loss_limit,
            KOrderTypeModel.take_profit_limit,
            KOrderTypeModel.trailing_stop_limit,
            KOrderTypeModel.stop_loss_and_limit,
        ]:
            model = KOrderDescrTwoPrice(
                pair=data["pair"],
                ordertype=data["ordertype"],
                price=data["price"],
                price2=data["price2"],
            )
        else:
            raise NotImplementedError

        # Finalize the order

        # optionally has a close order
        c = data.get("close")

        if data.get("abtype") == KABTypeModel.buy:
            finmodel = model.buy(leverage=data.get("leverage"), close=c)
        elif data.get("abtype") == KABTypeModel.sell:
            finmodel = model.sell(leverage=data.get("leverage"), close=c)
        else:
            raise NotImplementedError

        return finmodel

    @pre_dump
    def deconstruct_model(self, data, **kwargs):
        if callable(data.close):
            data.close = None  # dropping method before attempting dump
        return data

    @post_dump
    def filter_dict_ondump(self, data, **kwargs):
        data = {k: v for k, v in data.items() if v is not None}
        return data


@st.composite
def KDictStrategy(draw, model_strategy):
    model = draw(model_strategy)
    schema = KOrderDescrSchema()
    return schema.dump(model)


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
