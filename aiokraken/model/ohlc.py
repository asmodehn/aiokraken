from __future__ import annotations

# https://www.kraken.com/features/websocket-api#message-ohlc
from collections import namedtuple

import typing

""" A common data structure for OHLC based on pandas """
from datetime import datetime, timezone

import pandas as pd
# import pandas_ta as ta
import janitor

from ..utils.signal import Signal


OHLCValue = namedtuple("OHLCValue", ["datetime", "open", "high", "low", "close", "vwap", "volume", "count"])


class OHLC:

    def __init__(self, data: pd.DataFrame, last: typing.Union[datetime, int]):
        # if no datetime column => create it from time
        if 'time' in data and 'datetime' not in data:
            # necessary modifications that are not yet done by marshmallow
            data['datetime'] = pd.to_datetime(data.time, utc=True, unit='s')
        elif 'datetime' in data and (data.index != 'time'):
            data['time'] = data['datetime'].map(lambda dt: int(dt.timestamp()))

        # In both cases we want to make sure time is the index
        self.dataframe = data.set_index('time')

        # reorder columns
        self.dataframe = self.dataframe[["datetime", "open", "high", "low", "close", "vwap", "volume", "count"]]

        if not isinstance(last, datetime):
            # attempt conversion from timestamp
            self.last = datetime.fromtimestamp(last, tz = timezone.utc)
        else:
            self.last = last
        # TODO : remove last (always changing, moving indicators...)

        # TODO : take in account we only get last 720 intervals
        #  Ref : https://support.kraken.com/hc/en-us/articles/218198197-How-to-retrieve-historical-time-and-sales-trading-history-using-the-REST-API-Trades-endpoint-

        self.dataframe.close = pd.to_numeric(self.dataframe.close)
        self.dataframe.open = pd.to_numeric(self.dataframe.open)
        self.dataframe.high = pd.to_numeric(self.dataframe.high)
        self.dataframe.low = pd.to_numeric(self.dataframe.low)
        self.dataframe.vwap = pd.to_numeric(self.dataframe.vwap)
        self.dataframe.volume = pd.to_numeric(self.dataframe.volume)

    # TODO : we should probably provide "simple"/explicit interface to useful property of the dataframe ???

    @property
    def begin(self) -> datetime:
        return self.dataframe['datetime'].iloc[0]

    @property
    def end(self):
        return self.dataframe['datetime'].iloc[-1]

    @property
    def open(self):
        return self.dataframe['open'].iloc[0]

    @property
    def close(self):
        return self.dataframe['close'].iloc[-1]

    @property
    def high(self):
        return self.dataframe['high'].max()

    @property
    def low(self):
        return self.dataframe['low'].min()

    @property
    def volume(self):
        return self.dataframe['volume'].sum()

    def __repr__(self):
        # TODO : have a representation of OHLC that makes sense when '(de)composing' them...
        return f"<OHLC [{self.begin}..{self.end}] O/C [{self.open}..{self.close}] H/L [{self.high}..{self.low}] V {self.volume}>"

    # TODO : str representation (HOW ? graph on unicode string ???)

    def __eq__(self, other: OHLC):
        # check on len for optimization -> different length => different ohlc.
        return len(self) == len(other) and (self.dataframe == other.dataframe).all().all()  # we need exact match on 2 dimensions

    def __iter__(self):
        return self.dataframe.itertuples(name="IndexedOHLCValue")  # TODO some way of matching with actual OHLC values ?

    def __len__(self):
        return len(self.dataframe)

    # TODO : operator to split/merge and append/drop OHLC parts...  Ref https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html

    def stitch(self, other: OHLC):
        """ Stitching two OHLC together """

        # copying first
        old_df = self.dataframe.copy(deep=True)

        # marking duplicated rows (in first ?)
        for i, row in old_df.iterrows():
            dupval = False
            tup = OHLCValue(**row)

            for j, r in other.dataframe.iterrows():
                if OHLCValue(**r) == tup:
                    dupval = True
            old_df.at[i, 'dup'] = dupval

        filtered = old_df[old_df.dup == False]  # only picksrows where dup is False

        # concat order based on index (timestamps)
        if filtered.index[0] > other.dataframe.index[0]:
            newdf = pd.concat([other.dataframe, filtered], join='outer', sort=False)
        else:
            newdf = pd.concat([filtered, other.dataframe], join='outer', sort=False)

        newdf.drop('dup', axis=1, inplace=True)

        return OHLC(data=newdf, last=newdf.datetime.iloc[-1])

    def head(self):
        return self.dataframe.head()

    def macd(self, fast=None, slow=None, signal=None, offset=None, ):
        self.dataframe.ta.macd(fast=fast, slow=slow, signal=signal, offset=offset, append=True)

        return self

    def rsi(self, close=None, length=None, drift=None, offset=None ):
        self.dataframe.ta.rsi(close=close, length=length, drift=drift, offset=offset, append = True)

        return self

    def ema(self, close=None, length=None, offset=None, adjust=None, ):
        self.dataframe.ta.ema(close=close, length=length,  offset=offset,  adjust=adjust, append = True)

        return self

    # TODO: instance of OHLC will depend on chosen timeframe...

