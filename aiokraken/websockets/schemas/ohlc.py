

from dataclasses import dataclass

import typing

from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class OHLCUpdate:
    time: float  # Time, seconds since epoch
    etime: float  # End timestamp of the interval
    open: float  # Open price at midnight UTC
    high: float  # Intraday high price
    low: float  # Intraday low price
    close: float  # Closing price at midnight UTC
    vwap: float  # Volume weighted average price
    volume: float  # Accumulated volume today
    count: int  # Number of trades today


class OHLCUpdateSchema(BaseSchema):
    """
    >>> s= OHLCUpdateSchema()
    >>> s.load({
    ... 'connectionID': 12997236506998204415,
    ... 'event': 'systemStatus',
    ... 'status': 'online',
    ... 'version': '1.0.0'
    ... })
    KAsset(altname='ALTNAME', aclass='ACLASS', decimals=42, display_decimals=7)
    """
    time = fields.Float()
    etime = fields.Float()
    open = fields.Float()
    high = fields.Float()
    low = fields.Float()
    close = fields.Float()
    vwap = fields.Float()
    volume = fields.Float()
    count = fields.Integer()

    @post_load
    def build_model(self, data, **kwargs):
        a = OHLCUpdate(**data)
        return a

