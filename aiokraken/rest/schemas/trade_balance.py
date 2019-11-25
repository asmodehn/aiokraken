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
    equivalent_balance : str
    trade_balance : str
    margin: str
    net_pnl: str
    cost: str
    valuation:str
    equity : str
    free_margin : str
    margin_level : str

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
    equivalent_balance = fields.Str(data_key='eb')
    trade_balance = fields.Str(data_key='tb')
    margin = fields.Str(data_key='m')
    net_pnl = fields.Str(data_key='n')
    cost = fields.Str(data_key='c')
    valuation = fields.Str(data_key='v')
    equity = fields.Str(data_key='e')
    free_margin = fields.Str(data_key='mf')
    margin_level = fields.Str(data_key='ml')

    @post_load
    def build_model(self, data, **kwargs):
        return TradeBalance(**data)