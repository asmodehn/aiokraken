from __future__ import annotations
import typing
from collections import namedtuple
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
        # we merge on index (datetime)
        merged_df = pd.merge(self.timedataframe, other.timedataframe, right_index=True, left_index=True)

        # TODO : semantics ? copy or ref ?
        return EMA(df=merged_df, **self.params, **other.params)


def ema(name: str, length: int, offset:int, adjust: bool):

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


if __name__ == '__main__':

    print("bob")
