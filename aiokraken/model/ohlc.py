# https://www.kraken.com/features/websocket-api#message-ohlc

""" A common data structure for OHLC based on pandas """
from datetime import datetime

import pandas as pd
import pandas_ta as ta
import janitor

from ..utils.signal import Signal

class OHLC:

    def __init__(self, data: pd.DataFrame, last):
        self.dataframe = data
        self.last = last
        # TODO : remove last (always changing, moving indicators...)

        # TODO : take in account we only get last 720 intervals
        #  Ref : https://support.kraken.com/hc/en-us/articles/218198197-How-to-retrieve-historical-time-and-sales-trading-history-using-the-REST-API-Trades-endpoint-

        # necessary modifications that are not yet done by marshmallow
        self.dataframe.time = pd.to_datetime(self.dataframe.time, utc=True, unit='s')

        self.dataframe.close = pd.to_numeric(self.dataframe.close)
        self.dataframe.open = pd.to_numeric(self.dataframe.open)
        self.dataframe.high = pd.to_numeric(self.dataframe.high)
        self.dataframe.low = pd.to_numeric(self.dataframe.low)
        self.dataframe.volume = pd.to_numeric(self.dataframe.volume)

    # TODO : we should probably provide "simple"/explicit interface to useful property of the dataframe ???

    @property
    def begin(self) -> datetime:
        return self.dataframe['time'].iloc[0]

    @property
    def end(self):
        return self.dataframe['time'].iloc[-1]

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

    # TODO : operator to split/merge and append/drop OHLC parts...  Ref https://pandas.pydata.org/pandas-docs/stable/user_guide/merging.html

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