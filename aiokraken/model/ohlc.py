# https://www.kraken.com/features/websocket-api#message-ohlc

""" A common data structure for OHLC based on pandas """


import pandas as pd
import pandas_ta as ta
import janitor


class OHLC:

    def __init__(self, data: pd.DataFrame, last):
        self.dataframe = data
        self.last = last

        # necessary modifications that are not yet done by marshmallow
        self.dataframe.close = pd.to_numeric(self.dataframe.close)
        self.dataframe.open = pd.to_numeric(self.dataframe.open)
        self.dataframe.high = pd.to_numeric(self.dataframe.high)
        self.dataframe.low = pd.to_numeric(self.dataframe.low)

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
