# https://www.kraken.com/features/websocket-api#message-ohlc

""" A common data structure for OHLC based on pandas """


import pandas as pd

class OHLC:

    def __init__(self, data: pd.DataFrame, last):
        self.dataframe = data
        self.last = last

    def head(self):
        return self.dataframe.head()

    #TODO add (optional) technical analysis stuff here... (TAlib)
