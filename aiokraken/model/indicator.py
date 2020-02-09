from __future__ import annotations
import typing
from collections import namedtuple
from copy import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from dataclasses import dataclass, field

# from aiokraken.model.ohlc import OHLC/
import pandas as pd
import pandas_ta as ta  # necessary to access dataframe.ta
from aiokraken.model.ohlc import OHLC

from aiokraken.utils.timeindexeddataframe import TimeindexedDataframe


class Indicator:

    timedataframe: typing.Optional[TimeindexedDataframe]

    def __call__(self, ohlc_df: OHLC) -> Indicator:

        # TODO : compute all values with OHLC. no stitching, only ohlc takes care of that

        return self

    # Note: we delegate to timeframe for greater flexibility in usage.


#     """ Simple interface to be able to trigger signal from an indicator"""
#
#     def retrieve_signals(self, indicator):
#         self.signals += indicator.signals
#
#     def crossover(self, value_or_indicator: typing.Union[Decimal, Indicator]):
#         if isinstance(value_or_indicator, Decimal):
#             self.signals['crossover'].append(value_or_indicator)  # appending another signal to keep track of
#
#         elif isinstance(value_or_indicator, Indicator):
#             self.signals['crossover'].append(value_or_indicator)
#
#
#     # TODO : overload defaut stitcher ?

# TODO : OBV

EMA_params = namedtuple("EMA_params", ["length", "offset", "adjust"])

class EMA(Indicator):

    """ Container for technical indicators' dataframe.
    """
    # : this keeps the params in store for deterministic compute at a later stage
    params: typing.Dict[str, EMA_params]

    def __init__(self, df: TimeindexedDataframe, **params: EMA_params):

        self.params = params
        self.timedataframe = df

    def __call__(self, ohlc_df: OHLC) -> EMA:
        """ This is a time indexed dataframe, but updating itself not from itself, but from OHLC
            Meaning we recompute some time interval everytime,
            but its better to manage partial changes and fixes only in one place: OHLC model.
        """

        new_df = TimeindexedDataframe(
            pd.DataFrame(data={
                n: ohlc_df.dataframe.ta.ema(length=p.length, offset=p.offset, adjust=p.adjust)
                for n, p in self.params.items()
            },)
        )
        # TODO : convert columsn to proper dtype...

        return EMA(df=new_df, **self.params)  # reminder : Immutable semantics (like OHLC model at this level - not the mutable user interface)

    def __mul__(self, other: EMA):
        """ We can compose with other ema, this just adds a column.
        This is a categorical product, hence the use of *
        """

        # merging while avoiding duplicates...
        merging_params = self.params
        merged_df = copy(self.timedataframe)

        for n, p in other.params.items():
            if p not in self.params.values():  # dropping identical params
                merging_params.update({n: p})
                merged_df = merged_df * other.timedataframe[n]  # join with one column only

        # TODO : semantics ? copy or ref ?
        # CAREFUL with optimizations here, equality not trivial if we have nans...
        return EMA(df=merged_df, **merging_params)

    def __getitem__(self, item):
        if isinstance(item, str) and item in self.timedataframe.column:
            # return part of the dataframe as a dataframe
            return self.timedataframe[item].to_frame()
        elif isinstance(item, datetime):
            # return the element
            return self.timedataframe[item]
        elif isinstance(item, slice):
            # return the interval as a dataframe
            return self.timedataframe[item]

    def __len__(self):
        return len(self.timedataframe)


def ema(name: str, length: int, offset:int = 0, adjust: bool = False):

    p = EMA_params(length=length, offset=offset, adjust=adjust)
    # prepare timedataframe, but empty by default
    return EMA(df=TimeindexedDataframe(data=pd.DataFrame(columns=[name])), **{name: p})


#
#
# @dataclass(frozen=True)
# class MACD(Indicator):
#
#     fast: int
#     slow: int
#     signal: int
#     offset: int
#     data: pd.dataframe
#
#     def __call__(self, ohlc: OHLC) -> OHLC:
#         ohlc.dataframe.ta.macd(fast=self.fast, slow=self.slow, signal=self.signal, offset=self.offset, append=True)
#
#         return ohlc
#
#
# @dataclass(frozen=True)
# class RSI(Indicator):
#
#     close: int
#     length: int
#     drift: int
#     offset: int
#     data: pd.dataframe
#
#     def __call__(self, ohlc: OHLC) -> OHLC:
#
#         ohlc.dataframe.ta.rsi(close=self.close, length=self.length, drift=self.drift, offset=self.offset, append = True)
#
#         return ohlc


class Pivot:  # Note : this indicator is not a timeindexed dataframe...

    timeframe: timedelta
    R1: Decimal
    R2: Decimal
    R3: Decimal
    P: Decimal
    S1: Decimal
    S2: Decimal
    S3: Decimal

    def __init__(self, timeframe):
        self.timeframe = timeframe


if __name__ == '__main__':

    print("bob")
