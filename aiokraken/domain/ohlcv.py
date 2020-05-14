"""
Implementing a multiresolution timeindexed dataframe.
this is only useful for OHLCV and therefore it is a special case, for practicalities of implementation
"""
import asyncio
import typing
from datetime import datetime, timezone

import bokeh.layouts
import wrapt
from aiokraken.websockets.client import WssClient
from bokeh.io import output_file
from bokeh.models import CustomJS

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

    def fig(self):
        # TODO : buttons to switch between timeframes...

        from bokeh.models import RadioButtonGroup

        tfl = [KTimeFrameModel.one_day, KTimeFrameModel.one_hour, KTimeFrameModel.one_minute]

        radio_button_group = RadioButtonGroup(
            # TMP : only three main TF for now...
            labels=[tf.name for tf in tfl], active=0)

        # Note This will trigger data retrieval.
        plts = [self[tf].plot() for tf in tfl]

        callback = CustomJS(args=dict(dayref=plts[0],
                                      hourref=plts[1],
                                      minuteref=plts[2]), code="""
            var dayref_ok = dayref;
            var hourref_ok = hourref;
            var minuteref_ok = minuteref;
        """)

        radio_button_group.js_on_change('value', callback)

        self.layout = bokeh.layouts.column(#radio_button_group, BUGGY TODO: FIXIT
                                           bokeh.layouts.row(
                                               plts[0],
                                               plts[1],
                                               plts[2],
                                           ))

        return self.layout

    # TODO : extend to provide more ohlcv dataframes than the strict kraken API (via resampling from public trades history)


if __name__ == '__main__':

    from aiokraken.domain.pairs import AssetPairs

    from bokeh.plotting import output_file, save

    async def retrieve_pairs(pairs):
        return await AssetPairs.retrieve(pairs=pairs)

    ap = asyncio.run(retrieve_pairs(["XBT/EUR", "ETH/EUR"]))

    for p in ap:
        ohlcv = OHLCV(pair=p, rest=RestClient())
        f = ohlcv.fig()
        output_file(f"{p}.html", mode='inline')
        save(f)

