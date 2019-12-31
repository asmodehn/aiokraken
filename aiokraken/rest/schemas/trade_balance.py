import typing
import marshmallow
from decimal import Decimal
from marshmallow import fields, pre_load, post_load, validate

from .base import BaseSchema

from ..exceptions import AIOKrakenException
from ...model.ticker import Ticker, DailyValue, MinTrade, MinOrder

from collections import namedtuple
from dataclasses import dataclass, field
from decimal import Decimal

""" A common data structure for a Ticker """


@dataclass(frozen=True, init=True)
class TradeBalance:
    equivalent_balance : Decimal
    trade_balance : Decimal
    margin: Decimal
    net_pnl: Decimal
    cost: Decimal
    valuation: Decimal
    equity: Decimal
    free_margin: Decimal
    #margin_level: typing.Optional[str]  #missing sometimes ?

    # eb = equivalent balance (combined balance of all currencies)
    # tb = trade balance (combined balance of all equity currencies)
    # m = margin amount of open positions
    # n = unrealized net profit/loss of open positions
    # c = cost basis of open positions
    # v = current floating valuation of open positions
    # e = equity = trade balance + unrealized net profit/loss
    # mf = free margin = equity - initial margin (maximum margin available to open new positions)
    # ml = margin level = (equity / initial margin) * 100

    # TODO
    # def __repr__(self):
    #     return f"ask {self.ask.lot_volume} @ {self.ask.price} - bid {self.bid.lot_volume} @ {self.bid.price}"\
    #            f"today's open {self.todays_opening} high {self.high.today} low {self.low.today} close {self.last_trade_closed} volume {self.volume}"\
    #            f"{self.number_of_trades.today} trades @ vol_avg_price {self.volume_weighted_average_price.today}\n"


class TradeBalanceSchema(BaseSchema):
    equivalent_balance = fields.Decimal(data_key='eb', as_string=True)
    trade_balance = fields.Decimal(data_key='tb', as_string=True)
    margin = fields.Decimal(data_key='m', as_string=True)
    net_pnl = fields.Decimal(data_key='n', as_string=True)
    cost = fields.Decimal(data_key='c', as_string=True)
    valuation = fields.Decimal(data_key='v', as_string=True)
    equity = fields.Decimal(data_key='e', as_string=True)
    free_margin = fields.Decimal(data_key='mf', as_string=True)
    #margin_level = fields.Str(data_key='ml')  # can be missing (?)

    @post_load
    def build_model(self, data, **kwargs):
        return TradeBalance(**data)