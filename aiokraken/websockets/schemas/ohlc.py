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
    open: float  #Decimal  # Open price at midnight UTC
    high: float  # Decimal  # Intraday high price
    low: float  #Decimal  # Intraday low price
    close: float  #Decimal  # Closing price at midnight UTC
    vwap: float  #Decimal  # Volume weighted average price
    volume: float  #Decimal  # Accumulated volume today
    count: int  # Number of trades today

    def to_tidfrow(self):  # Goal : retrieved an indexed dataframe , suitable for appending to timeindexedDF
        datadict = dataclasses.asdict(self)
        assert datadict["time"] < datadict["etime"]  # to break early if it is not the case...
        datadict.pop("time")  # we don't actually care about the accurate time here

        datadict['datetime'] = pd.to_datetime(datadict['etime'], utc=True, unit='s')
        datadict.pop('etime')

        df = pd.DataFrame(datadict, index=[0])
        df.set_index('datetime', inplace=True)

        # for r in df.itertuples():
        #     print(r)

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
    open = fields.Float()  #Decimal(as_string=True)
    high = fields.Float()  #Decimal(as_string=True)
    low = fields.Float()  #Decimal(as_string=True)
    close = fields.Float()  # Decimal(as_string=True)
    vwap = fields.Float()  #Decimal(as_string=True)
    volume = fields.Float()  #Decimal(as_string=True)
    count = fields.Integer()

    @post_load
    def build_model(self, data, **kwargs):
        a = OHLCUpdate(**data)
        return a


if __name__ == '__main__':
    import doctest
    doctest.testmod()
