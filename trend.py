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


def trend_analysis(p: AssetPairModel, o: OHLCModel):
    # doing ema computation to get trend
    ema = o.ema(length=6)
    gradema = np.gradient(ema)

    # doing macd computation
    macddata = o.macd(fast=6, slow=12)
    gradmacd = np.gradient(macddata.MACDH_6_12_9)


    # # TODO : refine this !
    # if h4ema_6_closegrad[-1] > 0:
    #     # bullish
    #     print(f'{pair} bullish !')
    # else:
    #     # bearish
    #     print(f'{pair} bearish !')

    return gradema[-1], gradmacd[-1]

def correction_analysis(p: AssetPairModel, o: OHLCModel):
    # doing fidx computation and get correction
    efi = o.efi()
    gradefi = np.gradient(efi)

    obv = o.obv()
    gradobv = np.gradient(obv)

    return gradefi[-1], gradobv[-1]



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
        # TODO : use atr from ohlc class
        atrdata = po[KTimeFrameModel.one_day].atr(length=7)  # checking volatility during a week.
        acceptable_atr = 0.01 * po[KTimeFrameModel.one_day].close  # 1% of last closing price (today? yesterday?)
        if atrdata[-1] > acceptable_atr:  # ignored otherwise
            ohlcv[p] = po

    print(ohlcv)

    # TODO : Idea : heiken-hashi... to minimize noise...

    emagrad = dict()
    macdgrad = dict()
    efigrad = dict()
    obvgrad = dict()
    for p, o in ohlcv.items():
        emagrad[p], macdgrad[p] = trend_analysis(p, o[KTimeFrameModel.one_day])
        print(f"{p} trend : EMA {emagrad[p]} MACD {macdgrad[p]}")

        asyncio.run(o(interval=KTimeFrameModel.one_hour))
        efigrad[p], obvgrad[p] = correction_analysis(p, o[KTimeFrameModel.one_hour])

        print(f"{p} correction : EFI {efigrad[p]} OBV {obvgrad[p]}")

        # TODO : impulse system ?

        # CAREFUL : RuntimeError: Models must be owned by only a single document, Line(id='1284', ...) is already in a doc
        output_file(f"trend_{p}.html", mode='inline')
        # putting different timeframes side by side...
        save(row(o[KTimeFrameModel.one_day].layout, o[KTimeFrameModel.one_hour].layout))




