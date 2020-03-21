import dataclasses
from dataclasses import dataclass

import typing
from decimal import Decimal

from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema
import pandas as pd

from aiokraken.model.ohlc import OHLC


@dataclass(frozen=True)
class OHLCUpdate:
    time: float  # Time, seconds since epoch
    etime: float  # End timestamp of the interval
    open: Decimal  # Open price at midnight UTC
    high: Decimal  # Intraday high price
    low: Decimal  # Intraday low price
    close: Decimal  # Closing price at midnight UTC
    vwap: Decimal  # Volume weighted average price
    volume: Decimal  # Accumulated volume today
    count: int  # Number of trades today

    def to_tidfrow(self):  # Goal : retrieved an indexed dataframe , suitable for appending to timeindexedDF
        datadict = dataclasses.asdict(self)
        assert datadict["time"] < datadict["etime"]  # to break if it is not the case...
        datadict.pop("etime")

        datadict['datetime'] = pd.to_datetime(datadict['time'], utc=True, unit='s')
        datadict.pop('time')

        df = pd.DataFrame(datadict, index=[0])
        df.set_index('datetime', inplace=True)

        return df


class OHLCUpdateSchema(BaseSchema):
    """
    >>> s= OHLCUpdateSchema()
    >>> s.load({
    ... 'time': '1584781828.943175',
    ... 'etime': '1584781860.000000',
    ... 'open': '5710.20000',
    ... 'high': '5710.20000',
    ... 'low': '5702.10000',
    ... 'close': '5702.10000',
    ... 'vwap': '5704.85879',
    ... 'volume': '5.49849970',
    ... 'count': 20
    ... })
    OHLCUpdate(time=1584781828.943175, etime=1584781860.0, open=Decimal('5710.20000'), high=Decimal('5710.20000'), low=Decimal('5702.10000'), close=Decimal('5702.10000'), vwap=Decimal('5704.85879'), volume=Decimal('5.49849970'), count=20)
    """
    time = fields.Float()  # Time as float or decimal ? will float precision always be enough ?
    etime = fields.Float()
    open = fields.Decimal(as_string=True)
    high = fields.Decimal(as_string=True)
    low = fields.Decimal(as_string=True)
    close = fields.Decimal(as_string=True)
    vwap = fields.Decimal(as_string=True)
    volume = fields.Decimal(as_string=True)
    count = fields.Integer()

    @post_load
    def build_model(self, data, **kwargs):
        a = OHLCUpdate(**data)
        return a


if __name__ == '__main__':
    import doctest
    doctest.testmod()
