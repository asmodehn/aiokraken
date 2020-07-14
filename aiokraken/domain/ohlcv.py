"""
Implementing a multiresolution timeindexed dataframe.
this is only useful for OHLCV and therefore it is a special case, for practicalities of implementation
"""
import asyncio
import typing
from datetime import datetime, timezone

import bokeh.layouts
import wrapt

from bokeh.io import output_file
from bokeh.models import CustomJS, LayoutDOM

from aiokraken.domain.pairs import AssetPairs

from aiokraken.rest import RestClient
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.domain.models.ohlc import OHLC as OHLCModel


class OHLCV:
    """
    Class/Type to represent a multi-resolution OHLC.
    The type represents the complete retrievable ohlc over "all time, ever".
    An instance is a slice of it (on time axis), by default covering now and "a bit" (720 intervals) before.
    """

    # layout: bokeh.layouts.LayoutDOM

    _model: typing.Dict[KTimeFrameModel, OHLCModel]

    @classmethod
    async def retrieve(cls, pairs: AssetPairs, tfl: typing.List[KTimeFrameModel], rest: RestClient, loop = None):

        ohlcd = {tf: await OHLCModel.retrieve(pairs=pairs, timeframe=tf, restclient=rest) for tf in tfl}

        return cls(pairs=pairs, ohlc_dict=ohlcd, rest=rest, loop=loop)

    def __init__(self, pairs: AssetPairs, ohlc_dict: typing.Dict[KTimeFrameModel, OHLCModel], rest: RestClient, loop = None):

        self.rest = rest if rest is not None else RestClient()

        self.loop = loop if loop is not None else asyncio.get_event_loop()   # TODO : use restclient loop ??

        # TODO : get rid of these before : we are in ONE process, ONE thread => one client and one loop.

        self.pairs = pairs

        self._model = ohlc_dict

        # self._layouts = list()

    def __getitem__(self, item):

        # TODO pick closest timeframe
        # TODO  resample from it

        # to make sure we have uptodate & linked data...
        # TODO : replicate this design : allow both sync and async calls
        return self._model[item]

    def __iter__(self):
        return iter(self._model)

    async def __aiter__(self):
        # asynchronous iterator, to look forward the updates on this ohlc
        # TODO : this is where we setup websocket and forward any relevant message to the user...
        raise NotImplementedError


    # TODO : maybe the whole graphical output part should be in a separate (sub)package
    # def layout(self, doc=None) -> LayoutDOM:  # Note : doc is needed for updates
    #
    #     # we only draw the timeframe that we have !
    #     present_tf = {tf: ohlc for tf, ohlc in self._model.items() if ohlc.model}
    #
    #     p = OHLCVLayout(present_tf, doc=doc)
    #     self._layouts.append(p)
    #     return p._layout

    # TODO : extend to provide more ohlcv dataframes than the strict kraken API (via resampling from public trades history)


if __name__ == '__main__':

    from aiokraken.domain.pairs import AssetPairs

    from bokeh.plotting import output_file, save

    async def retrieve_pairs(pairs):
        return await AssetPairs.retrieve(pairs=pairs)

    ap = asyncio.run(retrieve_pairs(["XBT/EUR", "ETH/EUR"]))

    async def retrieve_ohlc(pairs, tfl):
        return await OHLCV.retrieve(pairs=pairs, tfl=tfl, rest=RestClient())

    ohlcv = asyncio.run(retrieve_ohlc(pairs=ap, tfl=[KTimeFrameModel.one_day, KTimeFrameModel.one_hour, KTimeFrameModel.one_minute]))

    # # defining indicators we want to use (before outputting report !)
    # ohlcv[KTimeFrameModel.one_day].ema(length=7)
    # ohlcv[KTimeFrameModel.one_hour].ema(length=24)
    # ohlcv[KTimeFrameModel.one_minute].ema(length=60)

    print("DAILY:")
    print(ohlcv[KTimeFrameModel.one_day])
    print("HOURLY:")
    print(ohlcv[KTimeFrameModel.one_hour])
    print("MINUTELY:")
    print(ohlcv[KTimeFrameModel.one_minute])

    # f = ohlcv.layout()
    # output_file(f"{p}.html", mode='inline')
    # save(f)

