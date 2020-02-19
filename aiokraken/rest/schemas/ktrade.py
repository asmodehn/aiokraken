
from dataclasses import dataclass, field
from datetime import datetime, MAXYEAR, MINYEAR
from decimal import Decimal
from enum import Enum

import hypothesis.strategies as st
import typing
from hypothesis.strategies import composite
from marshmallow import fields, post_load, pre_load

from .base import BaseSchema
from .kabtype import KABTypeModel, KABTypeField, KABTypeStrategy
from .kordertype import KOrderTypeModel, KOrderTypeField, KOrderTypeStrategy


@dataclass(frozen=True)
class KTradeModel:
    ordertxid: str  # order responsible for execution of trade
    pair: str  # asset pair
    time: int  # unix timestamp of trade
    type: KABTypeModel  # type of order (buy/sell)
    ordertype: KOrderTypeModel  # order type
    price: Decimal  # average price order was executed at (quote currency)
    cost: Decimal  # total cost of order (quote currency)
    fee: Decimal  # total fee (quote currency)
    vol: Decimal  # volume (base currency)
    margin: Decimal  # initial margin (quote currency)
    misc: str  #comma delimited list of miscellaneous info
        #closing = trade closes all or part of a position

    # iff the trade opened a position :
    postxid: typing.Optional[str] = None
    posstatus: typing.Optional[str] = None  # position status (open/closed)
    #     cprice = average price of closed portion of position (quote currency)
    #     ccost = total cost of closed portion of position (quote currency)
    #     cfee = total fee of closed portion of position (quote currency)
    #     cvol = total fee of closed portion of position (quote currency)
    #     cmargin = total margin freed in closed portion of position (quote currency)
    #     net = net profit/loss of closed portion of position (quote currency, quote currency scale)
    #     trades = list of closing trades for position (if available)

    trade_id: typing.Optional[str] = field(default=None)  # this will be set a bit after initialization

@composite
def KTradeStrategy(draw,
                      ordertxid= st.text(max_size=20),  # TODO : type for ordertxid ?
                      pair=st.text(max_size=8),
                   # NOte : to be able to store into pandas, we have to have compatible timestamps :
                   # Ref : https://github.com/pandas-dev/pandas/issues/28104
                      time=st.integers(min_value=int(datetime(year=1678, month=1, day=1).timestamp()),
                                       max_value=int(datetime(year=2261, month=12, day=31).timestamp())),
                      type=KABTypeStrategy(),
                      ordertype=KOrderTypeStrategy(),
                    price= st.decimals(allow_nan=False, allow_infinity=False),
                        cost= st.decimals(allow_nan=False, allow_infinity=False),
                        fee= st.decimals(allow_nan=False, allow_infinity=False),
                        vol= st.decimals(allow_nan=False, allow_infinity=False),
                        margin = st.decimals(allow_nan=False, allow_infinity=False),
                        misc= st.text(max_size=5),

                      postxid= st.one_of(st.none(),st.text(max_size=20)),  # TODO : type for postxid ?
                    posstatus=st.one_of(st.none(),st.text(max_size=5)),

                   trade_id=st.one_of(st.none(), st.text(max_size=20)),
):

    return KTradeModel(
        ordertxid = draw(ordertxid),
        pair = draw(pair),
        time= draw(time),
        type  =draw(type),
        ordertype= draw(ordertype),

        price= draw(price),
        cost=draw(cost),
        fee=draw(fee),

        vol=draw(vol),
        margin=draw(margin),

        misc=draw(misc),
        postxid = draw(postxid),
        posstatus=draw(posstatus),

        trade_id=draw(trade_id)
    )



class KTradeSchema(BaseSchema):

    ordertxid= fields.Str() # order responsible for execution of trade
    pair = fields.Str()  # asset pair
    time = fields.Integer(allow_none=True)  # unix timestamp of trade
    type = KABTypeField()  # type of order (buy/sell)
    ordertype = KOrderTypeField()  # order type
    price = fields.Decimal(as_string=True)  # average price order was executed at (quote currency)
    cost = fields.Decimal(as_string=True)  # total cost of order (quote currency)
    fee = fields.Decimal(as_string=True)  # total fee (quote currency)
    vol = fields.Decimal(as_string=True)  # volume (base currency)
    margin= fields.Decimal(as_string=True)  # initial margin (quote currency)
    misc=  fields.Str()  #comma delimited list of miscellaneous info
        #closing = trade closes all or part of a position

    # if the trade opened a position :
    postxid = fields.Str(allow_none=True, required=False)  # position txid... ?? (not in docs : https://www.kraken.com/features/api)
    posstatus = fields.Str(allow_none=True, required=False)  # position status (open/closed)
    #     cprice = average price of closed portion of position (quote currency)
    #     ccost = total cost of closed portion of position (quote currency)
    #     cfee = total fee of closed portion of position (quote currency)
    #     cvol = total fee of closed portion of position (quote currency)
    #     cmargin = total margin freed in closed portion of position (quote currency)
    #     net = net profit/loss of closed portion of position (quote currency, quote currency scale)
    #     trades = list of closing trades for position (if available)

    trade_id= fields.Str(allow_none=True)

    @post_load
    def build_model(self, data, **kwargs):
        return KTradeModel(**data)


@st.composite
def TradeDictStrategy(draw,
                          # Here we mirror arguments for the model strategy
                      ordertxid=st.text(max_size=20),
                      pair=st.text(max_size=8),
                      time=st.integers(min_value=int(datetime(year=1678, month=1, day=1).timestamp()),
                                       max_value=int(datetime(year=2261, month=12, day=31).timestamp())),
                      type=KABTypeStrategy(),
                      ordertype=KOrderTypeStrategy(),
                      price=st.decimals(allow_nan=False, allow_infinity=False),
                      cost=st.decimals(allow_nan=False, allow_infinity=False),
                      fee=st.decimals(allow_nan=False, allow_infinity=False),
                      vol=st.decimals(allow_nan=False, allow_infinity=False),
                      margin=st.decimals(allow_nan=False, allow_infinity=False),
                      misc=st.text(max_size=5),

                      postxid=st.one_of(st.none(),st.text(max_size=20)),
                      posstatus=st.one_of(st.none(),st.text(max_size=5)),

                      trade_id=st.one_of(st.none(), st.text(max_size=20))
                          ):
    model = draw(KTradeStrategy(
        ordertxid = ordertxid,
        postxid=postxid,
        pair = pair,
        time= time,
        type  =type,
        ordertype= ordertype,

        price= price,
        cost=cost,
        fee=fee,

        vol=vol,
        margin=margin,

        misc=misc,
        posstatus=posstatus,
        trade_id=trade_id
        )
    )
    schema = KTradeSchema()
    return schema.dump(model)


class TradeResponseSchema(BaseSchema):
    trades = fields.Dict(keys=fields.Str(), values=fields.Nested(KTradeSchema()))
    count = fields.Integer(allow_none=False)

    @pre_load
    def retrieve_id(self, data, many, partial):  # we must retreive the id in pre_load (before parsing to KLedgerInfoSchema
        for n in data['trades'].keys():
            data['trades'][n].setdefault("trade_id", n)
        return data

    @post_load
    def build_model(self, obj, many, partial):

        # we need to return the trades AND the total count (the trade response might be partial...)
        return obj['trades'], obj['count']  # Note we wont use any special type here for now TODO: maybe PartialPayload ?

        # TODO : dataframe for trades ? We have the time... we can have another (reversed) timeindexed dataframe...


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
