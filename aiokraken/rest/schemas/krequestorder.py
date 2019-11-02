import typing
from decimal import Decimal

from dataclasses import dataclass
from marshmallow import fields, pre_load, post_load, post_dump, pre_dump
from hypothesis import strategies as st


if not __package__:
    __package__ = 'aiokraken.rest.schemas'
from .base import BaseSchema
from .ktm import TMModel, TimerField
from aiokraken.model.kpair import PairModel, PairStrategy, PairField
from .kabtype import KABTypeModel, KABTypeField
from .kordertype import KOrderTypeModel, KOrderTypeField

#from ...model.order import Order, OpenOrder, RequestOrder

from .korderdescr import (
    KOrderDescr, KOrderDescrNoPrice, KOrderDescrOnePrice, KOrderDescrTwoPrice,
    KOrderDescrTwoPriceData,
    KOrderDescrNoPriceData,
    KOrderDescrOnePriceData,
    KOrderDescrNoPriceFinalized,
    KOrderDescrOnePriceFinalized,
    KOrderDescrTwoPriceFinalized,
    KOrderDescrNoPriceStrategy,
    KOrderDescrOnePriceStrategy,
    KOrderDescrTwoPriceStrategy,
    KOrderDescrCloseSchema,
)


#
# class OrderSchema(BaseSchema):
#
#     """ Schema to produce dict from model"""
#
#     type = fields.Str(required=True)
#     ordertype = fields.Str(required=True)
#
#     pair = fields.Str(required=True)
#     volume = fields.Decimal(required=True, as_string=True)
#     leverage = fields.Str()
#
#     starttm = fields.Str()
#     expiretm = fields.Str()
#
#     oflags = fields.List(fields.Str())
#
#     validate = fields.Bool()
#     userref = fields.Int()  # 32 bits signed number  # Ref : https://www.kraken.com/features/api#private-user-trading
#
#     close = fields.Str()
#
#     price = fields.Decimal(places=1, as_string=True)  # TODO : number of places likely depend on currency pair ?? 1 for BTC/EUR
#     price2 = fields.Decimal(places=1, as_string=True)
#

class OrderDescriptionSchema(BaseSchema):
    order = fields.Str(required=True)  # order description
    close = fields.Str()  # conditional close order description (if conditional close set)


class AddOrderResponseSchema(BaseSchema):
    descr = fields.Nested(OrderDescriptionSchema)
    txid = fields.List(fields.Str())  #array of transaction ids for order (if order was added successfully)


class CancelOrderResponseSchema(BaseSchema):
    pending = fields.List(fields.Str())
    count = fields.Integer()  #array of transaction ids for order (if order was added successfully)

#
# class OrderInfoSchema(BaseSchema):
#     pair = fields.Str()
#     type = fields.Str()  #(buy/sell)
#     ordertype = fields.Str()  #(See Add standard order)
#     price =fields.Number()
#     price2 = fields.Number()
#     leverage = fields.Str()  # ???
#     order = fields.Str()
#     close = fields.Str()


class AlreadyCalled(Exception):
    pass  # TODO

class OrderNotFinalized(Exception):
    pass # TODO


# TODO : Close Order
#     close[ordertype] = order type
#     close[price] = price
#     close[price2] = secondary price
# Maybe a base of orderdescr ???


@dataclass(frozen=True, init=False)
class RequestOrderMixin:
    pair: fields.String()

    fee_currency_base: bool  # TODO
    market_price_protection: bool  # TODO

    userref: typing.Optional[int]  # TODO

    # Explicit init to manage defaults without impacting inheritance...
    def __init__(self, pair: str, userref: typing.Optional[int] = None, fee_currency_base:bool = True, market_price_protection: bool = True, **kwargs):
        object.__setattr__(self, "pair", pair)
        object.__setattr__(self, "userref", userref)
        object.__setattr__(self, "fee_currency_base", fee_currency_base)
        object.__setattr__(self, "market_price_protection", market_price_protection)
        assert not kwargs, kwargs  # making sure we dont have any arguments left unprocessed


@dataclass(frozen=True, init=False)
class RequestOrderFinalizedMixin(RequestOrderMixin):

    volume: Decimal

    relative_starttm: typing.Optional[TMModel]
    relative_expiretm: typing.Optional[TMModel]

    # False by default to prevent accidental orders...
    validate: bool

    #
    def __init__(self, volume: Decimal, **kwargs):
        # default value to prevent any server order execution by default...
        object.__setattr__(self, "volume", volume)
        object.__setattr__(self, "validate", True)
        object.__setattr__(self, "relative_starttm", None)
        object.__setattr__(self, "relative_expiretm", None)
        super(RequestOrderFinalizedMixin, self).__init__(**kwargs)

    def delay(self, relative_starttm: TMModel = TMModel(0), relative_expiretm: TMModel = TMModel(0)):
        object.__setattr__(self, "relative_starttm", relative_starttm)
        object.__setattr__(self, "relative_expiretm", relative_expiretm)
        return self

    def execute(self, execute=False):
        object.__setattr__(self, "validate", not execute)
        return self


    # def cancel(self):
    #     #HOWTO ??
    #     # TODO : use self.txid
    #     return self


@dataclass(frozen=True, init=False)
class RequestOrderNoPriceMixin(RequestOrderMixin):
    descr: KOrderDescrNoPrice

    def __init__(self, descr: KOrderDescrNoPrice, **kwargs):
        object.__setattr__(self, "descr", descr)
        super(RequestOrderNoPriceMixin, self).__init__(**kwargs)


@dataclass(frozen=True, init=False)
class RequestOrderOnePriceMixin(RequestOrderMixin):
    descr: KOrderDescrOnePrice

    def __init__(self, descr: KOrderDescrOnePrice, **kwargs):
        object.__setattr__(self, "descr", descr)
        super(RequestOrderOnePriceMixin, self).__init__(**kwargs)


@dataclass(frozen=True, init=False)
class RequestOrderTwoPriceMixin(RequestOrderMixin):
    descr: KOrderDescrTwoPrice

    def __init__(self, descr: KOrderDescrTwoPrice, **kwargs):
        object.__setattr__(self, "descr", descr)
        super(RequestOrderTwoPriceMixin, self).__init__(**kwargs)


# Finalized classes bypass the incomplete class desc behavior, as desc is now of a different type...
@dataclass(frozen=True, init=False)
class RequestOrderNoPriceFinalized(RequestOrderFinalizedMixin):
    descr: KOrderDescrNoPriceFinalized

    def __init__(self, descr: KOrderDescrNoPriceFinalized, **kwargs):
        object.__setattr__(self, "descr", descr)
        super(RequestOrderNoPriceFinalized, self).__init__(**kwargs)


@dataclass(frozen=True, init=False)
class RequestOrderOnePriceFinalized(RequestOrderFinalizedMixin):
    descr: KOrderDescrOnePriceFinalized

    def __init__(self, descr: KOrderDescrOnePriceFinalized, **kwargs):
        object.__setattr__(self, "descr", descr)
        super(RequestOrderOnePriceFinalized, self).__init__(**kwargs)


@dataclass(frozen=True, init=False)
class RequestOrderTwoPriceFinalized(RequestOrderFinalizedMixin):
    descr: KOrderDescrTwoPriceFinalized

    def __init__(self, descr:KOrderDescrTwoPriceFinalized, **kwargs):
        object.__setattr__(self, "descr", descr)
        super(RequestOrderTwoPriceFinalized, self).__init__(**kwargs)


# Common "union" type for the finalized types
RequestOrderFinalized = RequestOrderFinalizedMixin


class RequestOrderNoPrice(RequestOrderNoPriceMixin):
    """
    """

    def buy(self, volume: Decimal,leverage: Decimal =Decimal(0), close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceData,
                KOrderDescrOnePriceData,
                KOrderDescrTwoPriceData,
            ]
        ] = None) -> RequestOrderNoPriceFinalized:
        return RequestOrderNoPriceFinalized(
            pair=self.pair,
            volume=volume,
            descr=self.descr.buy(leverage=leverage, close=close)
        )

    bid = buy

    def sell(self, volume: Decimal,leverage: Decimal=Decimal(0), close: typing.Optional[
            typing.Union[
                KOrderDescrNoPriceData,
                KOrderDescrOnePriceData,
                KOrderDescrTwoPriceData,
            ]
        ] = None,)-> RequestOrderNoPriceFinalized:
        return RequestOrderNoPriceFinalized(
            pair=self.pair,
            volume=volume,
            descr=self.descr.sell(leverage=leverage, close=close)
        )

    ask = sell


class RequestOrderOnePrice(RequestOrderOnePriceMixin):
    """
    """

    def buy(self, volume: Decimal, leverage: Decimal = Decimal(0), close: typing.Optional[
        typing.Union[
            KOrderDescrNoPriceData,
            KOrderDescrOnePriceData,
            KOrderDescrTwoPriceData,
        ]
    ] = None) -> RequestOrderOnePriceFinalized:
        return RequestOrderOnePriceFinalized(
            pair=self.pair,
            volume=volume,
            descr=self.descr.buy(leverage=leverage, close=close)
        )

    bid = buy

    def sell(self, volume: Decimal, leverage: Decimal = Decimal(0), close: typing.Optional[
        typing.Union[
            KOrderDescrNoPriceData,
            KOrderDescrOnePriceData,
            KOrderDescrTwoPriceData,
        ]
    ] = None, ) -> RequestOrderOnePriceFinalized:
        return RequestOrderOnePriceFinalized(
            pair=self.pair,
            volume=volume,
            descr=self.descr.sell(leverage=leverage, close=close)
        )

    ask = sell


class RequestOrderTwoPrice(RequestOrderTwoPriceMixin):

    def buy(self, volume: Decimal,leverage: Decimal = Decimal(0), close: typing.Optional[
        typing.Union[
            KOrderDescrNoPriceData,
            KOrderDescrOnePriceData,
            KOrderDescrTwoPriceData,
        ]
    ] = None) -> RequestOrderTwoPriceFinalized:
        return RequestOrderTwoPriceFinalized(
            pair=self.pair,
            volume=volume,
            descr=self.descr.buy(leverage=leverage, close=close)
        )

    bid = buy

    def sell(self, volume: Decimal ,leverage: Decimal = Decimal(0), close: typing.Optional[
        typing.Union[
            KOrderDescrNoPriceData,
            KOrderDescrOnePriceData,
            KOrderDescrTwoPriceData,
        ]
    ] = None, ) -> RequestOrderTwoPriceFinalized:
        return RequestOrderTwoPriceFinalized(
            pair=self.pair,
            volume=volume,
            descr=self.descr.sell(leverage=leverage, close=close)
        )

    ask = sell


@dataclass(frozen=True, init=False)
class RequestOrder(RequestOrderMixin):
    """
    # >>> RequestOrderModel(pair=PairModel(base=KCurrency.BTC, quote=KCurrency.EUR), volume=Decimal(0.01))  # # doctest:+ELLIPSIS
    TODO
    """

    def __init__(self,  pair: str, userref: typing.Optional[int] = None, fee_currency_base=True, market_price_protection=True):

        super(RequestOrder, self).__init__(pair=pair, userref=userref, fee_currency_base=fee_currency_base, market_price_protection=market_price_protection)

        # TODO
        # using default if nothing explicitely asked for
        # if False:  # TMP : oflags via params ?
        #     self.oflags = [
        #         'fcib' if fee_currency_base else 'fciq'
        #     ]  # WARNING : oflags formatting used to cause "InvalidkeyError" from the exchange...
        #     # TODO : address this...
        # if not market_price_protection:
        #     self.oflags.append('nompp')

    # Order type
    # Ref : From API docs :
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

    def market(self,):
        descr = KOrderDescr(pair=self.pair).market()
        return RequestOrderNoPrice(pair=descr.pair, descr = descr)

    def limit(self, limit_price):
        descr= KOrderDescr(pair=self.pair).limit(limit_price=limit_price)
        return RequestOrderOnePrice(pair=descr.pair, descr= descr )

    def stop_loss(self, stop_loss_price):
        descr = KOrderDescr(pair=self.pair).stop_loss(stop_loss_price=stop_loss_price)
        return RequestOrderOnePrice(pair=descr.pair, descr=descr)

    def take_profit(self, take_profit_price):
        descr= KOrderDescr(pair=self.pair).take_profit(take_profit_price=take_profit_price)
        return RequestOrderOnePrice(pair=descr.pair, descr=descr)

    def stop_loss_profit(self, stop_loss_price, take_profit_price):
        descr=KOrderDescr(pair=self.pair).stop_loss_profit(stop_loss_price=stop_loss_price, take_profit_price=take_profit_price)
        return RequestOrderTwoPrice(pair=descr.pair, descr=descr)

    def stop_loss_profit_limit(self, stop_loss_price, take_profit_price):
        descr=KOrderDescr(pair=self.pair).stop_loss_profit_limit(stop_loss_price=stop_loss_price, take_profit_price=take_profit_price)
        return RequestOrderTwoPrice(pair=descr.pair, descr=descr)

    def stop_loss_limit(self, stop_loss_trigger_price, triggered_limit_price):
        descr=KOrderDescr(pair=self.pair).stop_loss_limit(stop_loss_trigger_price=stop_loss_trigger_price, triggered_limit_price=triggered_limit_price)
        return RequestOrderTwoPrice(pair=descr.pair, descr=descr)

    def take_profit_limit(self, take_profit_trigger_price, triggered_limit_price):
        descr=KOrderDescr(pair=self.pair).take_profit_limit(take_profit_trigger_price=take_profit_trigger_price, triggered_limit_price=triggered_limit_price)
        return RequestOrderTwoPrice(pair=descr.pair, descr=descr)

    def trailing_stop(self, trailing_stop_offset):
        descr = KOrderDescr(pair=self.pair).trailing_stop(trailing_stop_offset=trailing_stop_offset)
        return RequestOrderOnePrice(pair=descr.pair, descr=descr)

    def trailing_stop_limit(self, trailing_stop_offset, triggered_limit_offset):
        descr = KOrderDescr(pair=self.pair).trailing_stop_limit(trailing_stop_offset=trailing_stop_offset, triggered_limit_offset=triggered_limit_offset)
        return RequestOrderTwoPrice(pair=descr.pair, descr=descr)

    def stop_loss_and_limit(self, stop_loss_price, limit_price):
        descr= KOrderDescr(pair=self.pair).stop_loss_and_limit(stop_loss_price=stop_loss_price, limit_price=limit_price)
        return RequestOrderTwoPrice(pair=descr.pair, descr=descr)

    def settle_position(self):
        descr = KOrderDescr(pair=self.pair).settle_position()
        return RequestOrderNoPrice(pair=descr.pair, descr=descr)


@st.composite
def RequestOrderStrategy(draw,):
    return RequestOrder(pair=draw(PairStrategy()), userref=draw(st.integers(min_value=0)), ) # TODO : add more arg for strategy, after implementation complete...


@st.composite
def RequestOrderNoPriceStrategy(draw,):

    rom = draw(RequestOrderStrategy())
    ot = draw(st.sampled_from([KOrderTypeModel.market, KOrderTypeModel.settle_position]))

    if ot == KOrderTypeModel.market:
        rop = rom.market()
    elif ot == KOrderTypeModel.settle_position:
        rop = rom.settle_position()
    else:
        raise NotImplementedError
    return rop


@st.composite
def RequestOrderOnePriceStrategy(draw,
    price=st.decimals(allow_nan=False, allow_infinity=False, min_value=1), ):

    rom = draw(RequestOrderStrategy())
    ot = draw(st.sampled_from([
                KOrderTypeModel.limit,
                KOrderTypeModel.take_profit,
                KOrderTypeModel.stop_loss,
                KOrderTypeModel.trailing_stop,]))

    if ot == KOrderTypeModel.limit:
        rop = rom.limit(limit_price=draw(price))
    elif ot == KOrderTypeModel.stop_loss:
        rop = rom.stop_loss(stop_loss_price=draw(price))
    elif ot == KOrderTypeModel.take_profit:
        rop = rom.take_profit(take_profit_price=draw(price))

    elif ot == KOrderTypeModel.trailing_stop:
        rop = rom.trailing_stop(trailing_stop_offset=draw(price))
    else:
        raise NotImplementedError
    return rop


@st.composite
def RequestOrderTwoPriceStrategy(draw,
    price=st.decimals(allow_nan=False, allow_infinity=False, min_value=1),
    price2=st.decimals(allow_nan=False, allow_infinity=False, min_value=1),):

    rom = draw(RequestOrderStrategy())
    ot = draw(st.sampled_from([
                KOrderTypeModel.stop_loss_profit,
                KOrderTypeModel.stop_loss_profit_limit,
                KOrderTypeModel.stop_loss_limit,
                KOrderTypeModel.take_profit_limit,
                KOrderTypeModel.trailing_stop_limit,
                KOrderTypeModel.stop_loss_and_limit,]))

    if ot == KOrderTypeModel.stop_loss_profit:
        rop = rom.stop_loss_profit(stop_loss_price=draw(price),
                             take_profit_price=draw(price2))
    elif ot == KOrderTypeModel.stop_loss_profit_limit:
        rop = rom.stop_loss_profit_limit(stop_loss_price=draw(price),
                                   take_profit_price=draw(price2))
    elif ot == KOrderTypeModel.stop_loss_limit:
        rop = rom.stop_loss_limit(stop_loss_trigger_price=draw(price),
                            triggered_limit_price=draw(price2))
    elif ot == KOrderTypeModel.take_profit_limit:
        rop = rom.take_profit_limit(
            take_profit_trigger_price=draw(price),
            triggered_limit_price=draw(price2))
    elif ot == KOrderTypeModel.trailing_stop_limit:
        rop = rom.trailing_stop_limit(trailing_stop_offset=draw(price),
                            triggered_limit_offset=draw(price2))
    elif ot == KOrderTypeModel.stop_loss_and_limit:
        rop = rom.stop_loss_and_limit(stop_loss_price=draw(price),
                            limit_price=draw(price2))
    else:
        raise NotImplementedError
    return rop


@st.composite
def RequestOrderFinalizeStrategy(
        draw,
        strategy,  # CAREFUL here ... how about typing strategies ???
        volume=st.decimals(allow_nan=False, allow_infinity=False, min_value=0),
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
        of = op.buy(volume=draw(volume), leverage=draw(leverage), close=c)
    elif oab == KABTypeModel.sell:
        of = op.sell(volume=draw(volume), leverage=draw(leverage), close=c)
    else:
        raise NotImplementedError

    return of


class RequestOrderSchema(BaseSchema):

    abtype = KABTypeField(required=True, data_key='type')  # need rename to not confuse python on this...
    ordertype = KOrderTypeField(required=True)

    pair= fields.String(required=False)  #PairField(required=False)  # to load/dump to/from internals of descr
    price = fields.Decimal(allow_nan=False, allow_infinity=False, as_string=True)
    price2 = fields.Decimal(allow_nan=False, allow_infinity=False, as_string=True)

    volume= fields.Decimal(allow_nan=False, allow_infinity=False, as_string=True)
    leverage= fields.Decimal(allow_nan=False, allow_infinity=False, as_string=True)
    relative_starttm= TimerField(required=False)
    relative_expiretm= TimerField(required=False)

    # TODO
    # fee_currency_base
    # market_price_protection

    userref= fields.Integer(required=False)  # TODO
    validate= fields.Bool(default=True)
    close= fields.Nested(KOrderDescrCloseSchema())  # TODO

    @pre_load
    def translate_fields(self, data, **kwargs):
        return data

    @post_load
    def build_model(self, data, **kwargs):

        # grab volume :
        volume = data.pop("volume")

        # grab validate :
        validate = data.pop("validate")

        # build order model
        rom= RequestOrder(**{
            'pair': data.get('pair'),
            'userref': data.get('userref'),
            # TODO fee_currency_base = True, market_price_protection = True
            }
        )

        ordertype = data.get('ordertype')
        price = data.get('price')
        price2 = data.get('price2')

        # and finalize step by step...
        if ordertype == KOrderTypeModel.market:
            pro = rom.market()
        elif ordertype == KOrderTypeModel.limit:
            pro = rom.limit(limit_price=price)
        elif ordertype == KOrderTypeModel.stop_loss:
            pro = rom.stop_loss(stop_loss_price=price)
        elif ordertype == KOrderTypeModel.take_profit:
            pro = rom.take_profit(take_profit_price=price)
        elif ordertype == KOrderTypeModel.stop_loss_profit:
            pro = rom.stop_loss_profit(stop_loss_price=price, take_profit_price=price2)
        elif ordertype == KOrderTypeModel.stop_loss_profit_limit:
            pro = rom.stop_loss_profit_limit(stop_loss_price=price, take_profit_price=price2)
        elif ordertype == KOrderTypeModel.stop_loss_limit:
            pro = rom.stop_loss_limit(stop_loss_trigger_price=price, triggered_limit_price=price2)
        elif ordertype == KOrderTypeModel.take_profit_limit:
            pro = rom .take_profit_limit(take_profit_trigger_price=price, triggered_limit_price=price2)
        elif ordertype == KOrderTypeModel.trailing_stop:
            pro = rom.trailing_stop(trailing_stop_offset=price)
        elif ordertype == KOrderTypeModel.trailing_stop_limit:
            pro = rom.trailing_stop_limit(trailing_stop_offset=price, triggered_limit_offset=price2)
        elif ordertype == KOrderTypeModel.stop_loss_and_limit:
            pro = rom.stop_loss_and_limit(stop_loss_price=price, limit_price=price2)
        elif ordertype == KOrderTypeModel.settle_position:
            pro = rom.settle_position()
        else:
            raise NotImplementedError

        abtype = data.get('abtype')

        if abtype == KABTypeModel.buy:
            ro = pro.buy(leverage=data.get('leverage'), volume=volume).execute(not validate)
        elif abtype == KABTypeModel.sell:
            ro = pro.sell(leverage=data.get('leverage'), volume=volume).execute(not validate)
        else:
            raise NotImplementedError

        return ro

    @pre_dump
    def make_dict(self, data, **kwargs):
        # in and out as model type. let marshmallow unpack the data from the dataclass
        return data

    @post_dump(pass_original=True)
    def cleanup_dict(self, data, original, **kwargs):
        # unpack descr content ## TODO : proper place ??
        #  Probably descr should not be in schema at all... only in model ?

        # TODO : better way to get marshmallow to call these by himself ??
        data.setdefault('ordertype', self.fields.get('ordertype').serialize('v', {'v': original.descr.ordertype}))
        data.setdefault('type', self.fields.get('abtype').serialize('v', {'v': original.descr.abtype}))
        data.setdefault('close', self.fields.get('close').serialize('v', {'v': original.descr.close}))

        # some way of Pattern matching would be nice here
        if hasattr(original.descr, "price"):
            data.setdefault('price', self.fields.get('price').serialize('v', {'v': original.descr.price}))

        if hasattr(original.descr, "price2"):
            data.setdefault('price2', self.fields.get('price2').serialize('v', {'v': original.descr.price2}))

        # Removing fields with default semantic to use server defaults, and minimize serialization errors
        if original.descr.leverage > 0:
            data.setdefault('leverage', self.fields.get('leverage').serialize('v', {'v': original.descr.leverage}))
        # else we do not set it (defaults to 'none' as per API docs)

        if data.get('relative_starttm') in ['', '+0']:
            data.pop('relative_starttm')
        if data.get('relative_expiretm') in ['', '+0']:
            data.pop('relative_expiretm')

        data = {k: v for k, v in data.items() if v is not None}

        return data


@st.composite
def KDictStrategy(draw, model_strategy):
    model = draw(model_strategy)
    schema = RequestOrderSchema()
    return schema.dump(model)
#
# @st.composite
# def RequestOrderDictStrategy(draw,
#                              pair=PairStrategy(),
#                              volume=st.decimals(allow_nan=False, allow_infinity=False),
#                              relative_starttm=TMStrategy(),
#                              relative_expiretm=TMStrategy(),
#                              userref=st.integers(),
#                              execute=st.sampled_from([False]),
#                              close=st.none(),
#                           ):
#     model = draw(RequestOrderStrategy(pair = pair,
#                       volume = volume,
#                       relative_starttm=relative_starttm,
#                       relative_expiretm=relative_expiretm,
#                       userref=userref,
#                       execute=execute,
#                       close=close,
#     ))
#     schema = RequestOrderSchema()
#     return schema.dump(model)


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
