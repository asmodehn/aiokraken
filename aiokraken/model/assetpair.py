import decimal
from dataclasses import dataclass

from aiokraken.model.asset import AssetClass
from hypothesis import strategies as st

@dataclass
class VolumeFee:
    volume: decimal.Decimal  # unit ??
    fee: decimal.Decimal  # pct


@dataclass
class AssetPair:

    altname: str  # alternate pair name
    wsname: str   # WebSocket pair name (if available)
    aclass_base: AssetClass  # asset class of base component
    base: str  # asset id of base component
    aclass_quote: str  # asset class of quote component
    quote: str  # asset id of quote component
    lot: str  # volume lot size
    pair_decimals: int  # scaling decimal places for pair
    lot_decimals: int  # scaling decimal places for volume
    lot_multiplier: int  # amount to multiply lot volume by to get currency volume
    leverage_buy: list  # array of leverage amounts available when buying
    leverage_sell: list  # array of leverage amounts available when selling
    fees: list  # fee schedule array in [volume, percent fee] tuples
    fees_maker: list  # maker fee schedule array in [volume, percent fee] tuples (if on maker/taker)
    fee_volume_currency: str  # volume discount currency
    margin_call: int  # margin call level
    margin_stop: int  # stop-out/liquidation margin level
