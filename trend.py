"""
This is a module implementing a simple trend analysis
"""
import asyncio
from dataclasses import dataclass

import numpy as np
import typing
from bokeh.layouts import layout, row, column
from bokeh.models import DataTable, ColumnDataSource, TableColumn, Label
from bokeh.plotting import figure

from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.model.ohlc import OHLC  as OHLCModel
from aiokraken.model.assetpair import AssetPair as AssetPairModel
from aiokraken.domain.ohlcv import OHLCV
from bokeh.io import output_file, save

from aiokraken.domain.pairs import AssetPairs

from aiokraken.rest import RestClient


# @dataclass()
# class Trend:
#     """
#     A data structure to accumulate information while we examine the different timeframes
#     """
#     pair: AssetPair  # must be len() == 1
#     ohlcv: OHLC
#     trend: int  # negative for bear, positive for bull, value is the derivative/taylor expansion
#     target: typing.Optional[Decimal]
#     forbid_buy: typing.Optional[bool]
#     forbid_sell: typing.Optional[bool]

    # TODO : goal : (structured) log all these somehow to identify buggy/useless trades or missed opportunities


def atr(ohlcv: OHLCModel, length):

    dups = ohlcv.index.duplicated()
    if dups.any():  # TODO : clean OHLCV data instead...
        raise RuntimeError(f"Duplicated data in OHLCV : {dups}")

    atrdata = ohlcv.ta.atr(length=length)

    atrp = figure(plot_height=120, tools='pan', x_axis_type="datetime", y_axis_location="right",
               sizing_mode="scale_width",)

    atrp.line(x=atrdata.index, y=atrdata.values, color='red')

    return atrdata, atrp


def trend_analysis(p: AssetPairModel, o: OHLCModel):
    # doing ema computation to get trend
    ema = o.ema(length=6)
    gradema = np.gradient(ema)

    # # TODO : refine this !
    # if h4ema_6_closegrad[-1] > 0:
    #     # bullish
    #     print(f'{pair} bullish !')
    # else:
    #     # bearish
    #     print(f'{pair} bearish !')

    report = column(
        o.figure,
    )

    output_file(f"trend_{p}.html", mode='inline')
    save(report)

    return gradema[-1]




# def trend_detect(pairs, rest = None):
#
#     rest = rest if rest is None else RestClient(server=Server())
#
#     # now looping on the pairs on the long timeframe
#
#     for pair, ohlcv in pairs.ohlcv(rest=rest).items():
#
#         # 1 determine trend (with a trend indicator, maybe MAs taylor expand, new high/new lows, etc.) over some period of time...
#
#         h4 = ohlcv.hours_4
#         # p = h4.plot()  # bokeh internal plot
#
#         h4d = h4.describe()
#         # TODO : CAREFUL with vwap at 0 sometimes !
#         print(h4d.mean()['close'])
#         print(h4d.std()['close'])
#         # TODO : check that std allows enough volatility to cover fees...
#
#         h4ema_6 = ohlcv.hours_4.ta.ema(length=6, offset=0)
#         h4ema_6_closegrad = np.gradient(h4ema_6)
#         # TODO : refine this !
#         if h4ema_6_closegrad[-1] > 0:
#             # bullish
#             print(f'{pair} bullish !')
#         else:
#             # bearish
#             print(f'{pair} bearish !')
#
#         # p = h4ema_6.plot()  # pandas matplotlib -> tkinter
#
#         # print(h4ema_6.describe())
#         # trend as int : taylor expand and  avg over a few timestamps...
#
#         # TODO
#
#         trend = Trend(pair=pair, ohlcv=ohlcv, trend=h4ema_6_closegrad[-1], target=None, forbid_buy=False, forbid_sell=False)
#
#         # 2 determine potential price target (usable if leverage >= 2 - always case when using positions - usually advantageous on intraday)
#
#         # TODO HOW ??
#
#
#         # 3 use impulse system to limit mistakes (ex: MA up + MACD up => do not sell)
#
#         # TODO
#
#         find_correction(trend)


if __name__ == '__main__':

    rest = RestClient()

    async def assets_retrieval(pairs):
        return await AssetPairs.retrieve(pairs=pairs, rest=rest)

    pairs = asyncio.run(assets_retrieval([
            "XBT/EUR",
            "ETH/EUR",
            # "XTZ/EUR",  #Duplicated index from kraken -> unusable until fix in OHLC Model here
        ])
    )

    async def ohlc_retrieval(pair, interval):
        return await OHLCV.retrieve(pair=pair, intervals=[interval if interval else KTimeFrameModel.one_day])

    ohlcv = dict()
    for p in pairs:
        po = asyncio.run(ohlc_retrieval(p, KTimeFrameModel.one_day))
        atrdata, atrp = atr(po[KTimeFrameModel.one_day], length=7)  # checking volitility during a week.
        acceptable_atr = 0.01 * po[KTimeFrameModel.one_day].close  # 1% of last closing price (today? yesterday?)
        if atrdata[-1] > acceptable_atr:  # ignored otherwise
            ohlcv[p] = po

    print(ohlcv)

    for p, o in ohlcv.items():
        result = trend_analysis(p, o[KTimeFrameModel.one_day])
        print(f"{p} trend : {result}")


