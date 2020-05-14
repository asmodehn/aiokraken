"""
Implementing a multiresolution timeindexed dataframe.
this is only useful for OHLCV and therefore it is a special case, for practicalities of implementation
"""
import asyncio
import typing
from datetime import datetime, timezone

import bokeh.layouts
import wrapt

from aiokraken.domain.layouts.ohlcv import OHLCVLayout
from aiokraken.websockets.client import WssClient
from bokeh.io import output_file
from bokeh.models import CustomJS, LayoutDOM

from aiokraken.model.assetpair import AssetPair

from aiokraken.rest import RestClient
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.domain.models.ohlc import OHLC as OHLCModel


class OHLCV:
    """
    Class/Type to represent a multi-resolution OHLC.
    The type represents the complete retrievable ohlc over "all time, ever".
    An instance is a slice of it (on time axis), by default covering now and "a bit" (720 intervals) before.
    """

    layout: bokeh.layouts.LayoutDOM

    _model: typing.Dict[KTimeFrameModel, OHLCModel]

    def __init__(self, pair: AssetPair, rest: RestClient, wsclient = None, loop = None):

        self.rest = rest if rest is not None else RestClient()

        self.loop = loop if loop is not None else asyncio.get_event_loop()   # TODO : use restclient loop ??
        self.wsclient = wsclient if wsclient is not None else WssClient(loop=self.loop)
        # TODO : get rid of these before : we are in ONE process, ONE thread => one client and one loop.

        self.pair = pair

        self._model = {tf: OHLCModel(pair=pair, timeframe=tf) for tf in KTimeFrameModel}

        self._layouts = list()

    def __getitem__(self, item):

        # TODO pick closest timeframe
        # TODO  resample from it

        # to make sure we have uptodate & linked data...
        # TODO : replicate this design : allow both sync and async calls
        if self.loop.is_running():
            return self.loop.create_task(self._model[item]())
        else:
            return self.loop.run_until_complete(self._model[item]())

    def __iter__(self):
        return iter(self._model)

    def layout(self, doc=None) -> LayoutDOM:  # Note : doc is needed for updates

        # we only draw the timeframe that we have !
        present_tf = {tf: ohlc for tf, ohlc in self._model.items() if ohlc.model}

        p = OHLCVLayout(present_tf, doc=doc)
        self._layouts.append(p)
        return p._layout

    # TODO : extend to provide more ohlcv dataframes than the strict kraken API (via resampling from public trades history)


if __name__ == '__main__':

    from aiokraken.domain.pairs import AssetPairs

    from bokeh.plotting import output_file, save

    async def retrieve_pairs(pairs):
        return await AssetPairs.retrieve(pairs=pairs)

    ap = asyncio.run(retrieve_pairs(["XBT/EUR", "ETH/EUR"]))

    for p in ap:
        ohlcv = OHLCV(pair=p, rest=RestClient())

        for tf in [KTimeFrameModel.one_day, KTimeFrameModel.one_hour, KTimeFrameModel.one_minute]:
            asyncio.run(ohlcv[tf]())

        f = ohlcv.layout()
        output_file(f"{p}.html", mode='inline')
        save(f)

