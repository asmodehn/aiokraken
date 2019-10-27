import functools
import typing
from decimal import Decimal
from enum import Enum
import marshmallow
from dataclasses import dataclass, field, asdict
from marshmallow import fields, pre_load, post_load, post_dump, pre_dump
from hypothesis import given, strategies as st

from aiokraken.rest.schemas.ktm import TMStrategy, TimerField

if not __package__:
    __package__ = 'aiokraken.rest.schemas'
from .base import BaseSchema
from .kpair import PairModel, PairStrategy, PairField
from .kabtype import KABTypeModel
from .kordertype import KOrderTypeModel

from ..exceptions import AIOKrakenException
#from ...model.order import Order, OpenOrder, RequestOrder

from .kopenorder import KOpenOrderSchema
from .korderdescr import KOrderDescrModel, KOrderDescrSchema

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


@dataclass(init=False)
class RequestOrderModel:
    """
    >>> RequestOrderModel(pair='EURBTC', volume=0.01)  # # doctest:+ELLIPSIS
    RequestOrderModel(descr=functools.partial(<function BaseSchema.load at ...>, pair='EURBTC'), volume=0.01, relative_starttm=0, relative_expiretm=0, userref=None, close=None, execute=False)
    """
    # TODO : Somehow merge part of this with openorder ??? if we can ignore differences...

    _descr_data: typing.Dict = field(repr=False)
    _descr: typing.Union[None, KOrderDescrModel]

    volume: Decimal
    # leverage: Decimal  # TODO or NOT
    relative_starttm: int
    relative_expiretm: int

    # fee_currency_base
    # market_price_protection

    userref: typing.Optional[int]  # TODO
    close: typing.Optional[str]  # TODO
    execute: bool = False

    def __init__(self,  pair, volume, relative_starttm = 0, relative_expiretm = 0, userref = None, execute=False, close= None, fee_currency_base=True, market_price_protection=True):

        # TODO : maybe get rid of this ?
        self._descr_schema = KOrderDescrSchema()  # storing schema to load descr content

        self._descr_data = {'pair': pair}
        self._descr = None

        # Note we probably want to minimize data stored here, if it matches default behavior on kraken, in order to side step potential formatting issues...
        self.volume = volume

        self.relative_starttm = relative_starttm
        self.relative_expiretm = relative_expiretm

        self.execute = execute
        # these are optional member
        self.userref = userref
        self.close = close

        # TODO
        # using default if nothing explicitely asked for
        # if False:  # TMP : oflags via params ?
        #     self.oflags = [
        #         'fcib' if fee_currency_base else 'fciq'
        #     ]  # WARNING : oflags formatting used to cause "InvalidkeyError" from the exchange...
        #     # TODO : address this...
        # if not market_price_protection:
        #     self.oflags.append('nompp')

    @property
    def pair(self):
        if self._descr_data:
            return self._descr_data['pair']
        else:
            return self._descr.pair

    # Declaring intent progressively via methods

    @property
    def descr(self):
        if self._descr is None:
            if 'abtype' in self._descr_data and 'ordertype' in self._descr_data:
                # if we have both abtype and ordertype we want to create the descr instance
                # Note we do not want to use the schema here, as we are only dealing with internal values
                self._descr = KOrderDescrModel(**self._descr_data)
                self._descr_data = None
        # In any case return _descr. None means order incomplete. whether this is relevant or not depends on the caller.
        return self._descr

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
        self._descr_data.update({'ordertype': KOrderTypeModel.market})
        return self

    def limit(self, limit_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.limit, 'price': limit_price})
        return self

    def stop_loss(self, stop_loss_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.stop_loss, 'price': stop_loss_price})
        return self

    def take_profit(self, take_profit_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.take_profit, 'price': take_profit_price})
        return self

    def stop_loss_profit(self, stop_loss_price, take_profit_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.stop_loss_profit, 'price': stop_loss_price, 'price2': take_profit_price})
        return self

    def stop_loss_profit_limit(self, stop_loss_price, take_profit_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.stop_loss_profit_limit, 'price': stop_loss_price, 'price2': take_profit_price})
        return self

    def stop_loss_limit(self, stop_loss_trigger_price, triggered_limit_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.stop_loss_limit, 'price': stop_loss_trigger_price, 'price2': triggered_limit_price})
        return self

    def take_profit_limit(self, take_profit_trigger_price, triggered_limit_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.take_profit_limit,  'price': take_profit_trigger_price, 'price2': triggered_limit_price})
        return self

    def trailing_stop(self, trailing_stop_offset):
        self._descr_data.update({'ordertype': KOrderTypeModel.trailing_stop, 'price': trailing_stop_offset})
        return self

    def trailing_stop_limit(self, trailing_stop_offset, triggered_limit_offset):
        self._descr_data.update({'ordertype': KOrderTypeModel.trailing_stop_limit, 'price': trailing_stop_offset, 'price2': triggered_limit_offset})
        return self

    def stop_loss_and_limit(self, stop_loss_price, limit_price):
        self._descr_data.update({'ordertype': KOrderTypeModel.stop_loss_and_limit, 'price': stop_loss_price, 'price2': limit_price})
        return self

    def settle_position(self):
        self._descr_data.update({'ordertype': KOrderTypeModel.settle_position})
        return self

    # Ask/Bid type

    def buy(self, leverage=0):
        self._descr_data.update({'abtype': KABTypeModel.buy, 'leverage': leverage})
        return self

    bid = buy

    def sell(self, leverage=0):
        self._descr_data.update({'abtype': KABTypeModel.sell, 'leverage': leverage})
        return self

    ask = sell

    def cancel(self):
        #HOWTO ??
        # TODO : use self.txid
        return self


@st.composite
def RequestOrderStrategy(draw,
                         pair = PairStrategy(),
                         volume = st.decimals(allow_nan=False, allow_infinity=False),
                         relative_starttm=TMStrategy(),
                         relative_expiretm=TMStrategy(),
                         userref=st.integers(),
                         execute=st.sampled_from([False]),
                         close=st.none(),
                         type= st.sampled_from(KABTypeModel),
                         ordertype = st.sampled_from(KOrderTypeModel)
                         ):

    rom = RequestOrderModel(
        pair = draw(pair),
        volume=draw(volume),
        relative_starttm= draw(relative_starttm),
        relative_expiretm=draw(relative_expiretm),
        userref=draw(userref),
        execute=draw(execute),
        close=draw(close)
    )

    ot = draw(ordertype)
    t = draw(type)
    if ot == KOrderTypeModel.market:
        rom.market()
    elif ot == KOrderTypeModel.limit:
        rom.limit(limit_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.stop_loss:
        rom.stop_loss(stop_loss_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.take_profit:
        rom.take_profit(take_profit_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.stop_loss_profit:
        rom.stop_loss_profit(stop_loss_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)), take_profit_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.stop_loss_profit_limit:
        rom.stop_loss_profit_limit(stop_loss_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)),
                             take_profit_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.stop_loss_limit:
        rom.stop_loss_limit(stop_loss_trigger_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)), triggered_limit_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.take_profit_limit:
        rom.take_profit_limit(take_profit_trigger_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)), triggered_limit_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.trailing_stop:
        rom.trailing_stop(trailing_stop_offset=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.trailing_stop_limit:
        rom.trailing_stop_limit(trailing_stop_offset=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)), triggered_limit_offset=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.stop_loss_and_limit:
        rom.stop_loss_and_limit(stop_loss_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)), limit_price=draw(st.decimals(allow_nan=False, allow_infinity=False, min_value= 1)))
    elif ot == KOrderTypeModel.settle_position:
        rom.settle_position()
    else:
        raise NotImplementedError

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

    if t == KABTypeModel.buy:
        rom.buy()
    elif t == KABTypeModel.sell:
        rom.sell()
    else: # should never happen
        rom.sell()

    return rom


class RequestOrderSchema(BaseSchema):
    descr= fields.Nested(KOrderDescrSchema())
    pair= PairField(required=False)  # to load/dump to/from internals of descr

    volume= fields.Decimal()
    leverage= fields.Decimal()
    relative_starttm= TimerField()
    relative_expiretm= TimerField()

    # fee_currency_base
    # market_price_protection

    userref= fields.Integer()  # TODO
    execute= fields.Bool(default=False)
    close= fields.Str()  # TODO

    @pre_load
    def translate_fields(self, data, **kwargs):
        data.setdefault('execute', not data.get('validate'))
        data.pop('validate')
        return data

    @post_load
    def build_model(self, data, **kwargs):
        descr = data.pop('descr')

        # grab the pair from descr
        data['pair'] = descr.pair
        # build order model
        rom= RequestOrderModel(**data)

        # and finalize step by step...
        if descr.ordertype == KOrderTypeModel.market:
            rom.market()
        elif descr.ordertype == KOrderTypeModel.limit:
            rom.limit(limit_price=descr.price)
        elif descr.ordertype == KOrderTypeModel.stop_loss:
            rom.stop_loss(stop_loss_price=descr.price)
        elif descr.ordertype == KOrderTypeModel.take_profit:
            rom.take_profit(take_profit_price=descr.price)
        elif descr.ordertype == KOrderTypeModel.stop_loss_profit:
            rom.stop_loss_profit(stop_loss_price=descr.price, take_profit_price=descr.price2)
        elif descr.ordertype == KOrderTypeModel.stop_loss_profit_limit:
            rom.stop_loss_profit_limit(stop_loss_price=descr.price, take_profit_price=descr.price2)
        elif descr.ordertype == KOrderTypeModel.stop_loss_limit:
            rom.stop_loss_limit(stop_loss_trigger_price=descr.price, triggered_limit_price=descr.price2)
        elif descr.ordertype == KOrderTypeModel.take_profit_limit:
            rom .take_profit_limit(take_profit_trigger_price=descr.price, triggered_limit_price=descr.price2)
        elif descr.ordertype == KOrderTypeModel.trailing_stop:
            rom.trailing_stop(trailing_stop_offset=descr.price)
        elif descr.ordertype == KOrderTypeModel.trailing_stop_limit:
            rom.trailing_stop_limit(trailing_stop_offset=descr.price, triggered_limit_offset=descr.price2)
        elif descr.ordertype == KOrderTypeModel.stop_loss_and_limit:
            rom.stop_loss_and_limit(stop_loss_price=descr.price, limit_price=descr.price2)
        elif descr.ordertype == KOrderTypeModel.settle_position:
            rom.settle_position()
        else:
            raise NotImplementedError

        if descr.abtype == KABTypeModel.sell:
            rom.buy(leverage=descr.leverage)
        elif descr.abtype == KABTypeModel.sell:
            rom.sell(leverage=descr.leverage)
        return rom

    @pre_dump
    def make_dict(self, data, **kwargs):

        # accessing descr property to build it if needed
        descr = data.descr

        def filter_none(item_list):
            return {k: v for k, v in item_list if v is not None if not k.startswith('_')}

        d = asdict(data, dict_factory=filter_none)

        # Adding redundant fields
        d.setdefault('pair', data.descr.pair)
        d.setdefault('descr', descr)

        return d

    @post_dump
    def cleanup_dict(self, data, **kwargs):

        # translating
        data.setdefault('validate', not data.get('execute'))
        data.pop('execute')

        # Removing fields with default semantic to use server defaults, and minimize serialization errors
        if data.get('relative_starttm') == '+0':
            data.pop('relative_starttm')
        if data.get('relative_expiretm') == '+0':
            data.pop('relative_expiretm')

        return data


@st.composite
def RequestOrderDictStrategy(draw,
                             pair=PairStrategy(),
                             volume=st.decimals(allow_nan=False, allow_infinity=False),
                             relative_starttm=TMStrategy(),
                             relative_expiretm=TMStrategy(),
                             userref=st.integers(),
                             execute=st.sampled_from([False]),
                             close=st.none(),
                          ):
    model = draw(RequestOrderStrategy(pair = pair,
                      volume = volume,
                      relative_starttm=relative_starttm,
                      relative_expiretm=relative_expiretm,
                      userref=userref,
                      execute=execute,
                      close=close,
    ))
    schema = RequestOrderSchema()
    return schema.dump(model)


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
