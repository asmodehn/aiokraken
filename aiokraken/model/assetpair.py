import decimal
from dataclasses import dataclass, field, asdict

import typing

from aiokraken.model.asset import AssetClass
from hypothesis import strategies as st

@dataclass
class VolumeFee:
    volume: decimal.Decimal  # unit ??
    fee: decimal.Decimal  # pct


@dataclass(frozen=True)
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
    leverage_buy: list = field(compare=False)  # array of leverage amounts available when buying (not used in comparison)
    leverage_sell: list = field(compare=False)  # array of leverage amounts available when selling (not used in comparison)
    fees: list = field(compare=False)  # fee schedule array in [volume, percent fee] tuples (not used in comparison)
    fees_maker: list = field(compare=False)  # maker fee schedule array in [volume, percent fee] tuples (if on maker/taker) (not used in comparison)
    fee_volume_currency: str  # volume discount currency
    margin_call: int  # margin call level
    margin_stop: int  # stop-out/liquidation margin level
    restname: typing.Optional[str] = field(default=None, )  # this will be set a bit after initialization

    def __call__(self, restname):  # for late naming
        newdata = asdict(self)
        newdata.update({'restname': restname})
        return AssetPair(**newdata)
