from dataclasses import dataclass, field
from enum import Enum

import typing


class AssetClass(Enum):
    """

    """
    # currency
    currency = 'currency'

    def __str__(self) -> str:
        """Kraken default representation for sending data."""
        return f'{self.value}'

    def __repr__(self) -> str:
        """Internal representation, unique."""
        return f'{self.name}'


@dataclass
class Asset:
    altname: str  # alternate name
    aclass: str  # asset class
    decimals: int  # scaling decimal places for record keeping
    display_decimals: int  # scaling decimal places for output display
    restname: typing.Optional[str] = field(default=None)  # this will be set a bit after initialization

