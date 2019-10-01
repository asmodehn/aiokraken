# https://www.kraken.com/features/websocket-api#message-ohlc

""" A common data structure for OHLC based on pandas """


import pandas as pd
import pandas_ta as ta
import janitor

class OHLC:

    def __init__(self, data: pd.DataFrame, last):
        self.dataframe = data
        self.last = last

    def head(self):
        return self.dataframe.head()

    def macd(self, fast=None, slow=None, signal=None, offset=None, ):
        macd = self.dataframe.ta.macd(fast=fast, slow=slow, signal=signal, offset=offset)

        # TODO add time
        self.dataframe = self.dataframe.join(macd)

        return self