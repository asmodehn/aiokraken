from __future__ import annotations

# https://www.kraken.com/features/websocket-api#message-ohlc
from collections import namedtuple

import typing

""" A common data structure for OHLC based on pandas """
from datetime import datetime, timezone

import pandas as pd
# CAREFUL to what we are doing
pd.set_option('mode.chained_assignment','raise')
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
            data['time'] = data['datetime'].map(lambda dt: dt.timestamp())

        # making sure times are integers.
        data.time = pd.to_numeric(data.time, downcast='integer')
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

        newdf_noidx = self.dataframe.reset_index().merge(other.dataframe.reset_index(), how='outer', sort=True)

        # newdf = newdf_noidx.groupby('time') # This works on axis=0, not what we want...

        def stitcher(row: pd.Series):
            nonlocal newdf_noidx

            #retrieving the index by matching time
            rows = newdf_noidx.loc[newdf_noidx['time'] == row['time']]

            if len(rows) > 1:
                chosen = None
                prev = newdf_noidx.loc[rows.index[0] - 1]
                next = newdf_noidx.loc[rows.index[1] + 1]

                # handling differences on count, open and close

                if rows.iloc[0]['count'] > rows.iloc[1]['count']:
                    chosen = rows.iloc[0].copy()
                elif rows.iloc[0]['count'] < rows.iloc[1]['count']:
                    chosen = rows.iloc[1].copy()

                if rows.iloc[0]['open'] != rows.iloc[1]['open']:
                    # open is different -> pick the value that is closets to the previous close
                    delta = [None, None]
                    delta[0] = abs(prev['close'] - rows.iloc[0]['open'])
                    delta[1] = abs(prev['close'] - rows.iloc[1]['open'])
                    if delta[1] < delta[0]:
                        if chosen is not None and not (chosen == rows.iloc[1]).all():  # need to merge !
                            chosen['open'] = rows.iloc[1]['close']
                        else:
                            chosen = rows.iloc[1].copy()
                    else:
                        if chosen is not None and not (chosen == rows.iloc[0]).all():  # need to merge !
                            chosen['close'] = rows.iloc[0]['close']
                        else:
                            chosen = rows.iloc[0].copy()

                if rows.iloc[0]['close'] != rows.iloc[1]['close']:
                    # close is different-> pick the value that is closest to the previous close
                    delta = [None, None]
                    delta[0] = abs(next['open'] - rows.iloc[0]['close'])
                    delta[1] = abs(next['open'] - rows.iloc[1]['close'])
                    if delta[1] < delta[0]:
                        if chosen is not None and not (chosen == rows.iloc[1]).all():  # need to merge !
                                chosen['close'] = rows.iloc[1]['close']
                        else:
                            chosen = rows.iloc[1].copy()
                    else:
                        if chosen is not None and not (chosen == rows.iloc[0]).all():  # need to merge !
                                chosen['close'] = rows.iloc[0]['close']
                        else:
                            chosen = rows.iloc[0].copy()

                if chosen is None:
                    print(rows)

                # optionally change high and low
                chosen['high'] = max(chosen['high'], chosen['open'], chosen['close'])
                chosen['low'] = min(chosen['low'], chosen['open'], chosen['close'])

                row = chosen

            return row



        # rolling axis=1 seems buggy on 0.25.3
        #agged = newdf.rolling(3, axis=1).agg(stitcher, axis=1)
        newdf = newdf_noidx.agg(stitcher, axis=1).drop_duplicates().set_index('time')

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

