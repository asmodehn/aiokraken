from dataclasses import dataclass
from enum import Enum


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
    #name: str  # name
    altname: str  # alternate name
    aclass: str  # asset class
    decimals: int  # scaling decimal places for record keeping
    display_decimals: int  # scaling decimal places for output display

