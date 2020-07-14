from __future__ import annotations
import asyncio
import dataclasses
import functools
import os
from collections import namedtuple, deque
from datetime import timedelta, datetime, timezone

import typing
from decimal import Decimal

import pandas as pd
import wrapt
from aiokraken.domain.pairs import AssetPairs

from aiokraken.websockets.publicapi import ohlc
from livebokeh.datamodel import DataModel

# from bokeh_ta.macd import macd as macd_plot
# from bokeh_ta.ohlc import ohlc as ohlc_plot

from bokeh.io import output_file, save
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, LayoutDOM, Column
from bokeh.plotting import figure, Figure
from bokeh.themes import Theme


from aiokraken.model.assetpair import AssetPair

from aiokraken.model.indicator import Indicator, EMA_params

from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.model.ohlc import OHLC as OHLCModel, OHLCValue
from aiokraken.model.indicator import ema, EMA as EMAModel
from aiokraken.websockets.schemas.ohlc import OHLCUpdate
from collections.abc import Mapping

from aiokraken.utils.filter import Filter


Pivot = namedtuple("Pivot", ["pivot", "R1", "R2", "R3", "S1", "S2", "S3"])


class OHLC:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the time axis... probably via the callable / iterator protocols
        It is also encapsulating the timeframe concept, and therefore should behave like a directed container
        on the time *interval* axis (nagivating between timeframes), probably via mapping protocol...
    """

    models: typing.Dict[AssetPair, OHLCModel]
    # updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    # validtime: timedelta

    # list of indicators used, in order to plot them on request.
    indicators: typing.List[typing.Callable]

    @classmethod
    async def retrieve(cls, pairs: AssetPairs, timeframe: KTimeFrameModel, restclient: RestClient, loop=None):
        ohlcmodels = dict()

        for p in pairs:
            # TODO : validate the pair using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
            ohlcmodels[p] = await restclient.ohlc(pair=p, interval=timeframe)

        # we need to async retrieve model before building instance
        ohlc = OHLC(timeframe=timeframe, pair_ohlcmodels=ohlcmodels,restclient=restclient, loop=loop)

        return ohlc

    # TODO : get rid of async on initialization.
    #  HOW : provide storage, and upon initialization, retrieve data from storage.
    #  IMPLIES : we must allow for an "empty" instance to be created, and be updated afterwards.
    #  Note : Not really useful until cold data storage is available... in the meantime, it is just a minor annoyance.
    def __init__(self, timeframe: KTimeFrameModel, pair_ohlcmodels: typing.Dict[AssetPair, OHLCModel], restclient: RestClient = None, loop=None):
        self.models = pair_ohlcmodels

        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...

        self.loop = loop if loop is not None else asyncio.get_event_loop()   # TODO : use restclient loop ??
        # defaults to have a websocket client

        # self.validtime = valid_time   # None means always valid
        self.timeframe = timeframe


        # self.indicators = list()

        # self._plots = list()

        self.callback(self._update)

    @property
    def begin(self) -> typing.Dict[AssetPair,datetime]:
        return {p: m.begin for p, m in self.models.items()}

    @property
    def end(self) -> typing.Dict[AssetPair,datetime]:
        return {p: m.end for p, m in self.models.items()}

    @property
    def open(self) -> typing.Dict[AssetPair,Decimal]:
        return {p: m.open for p, m in self.models.items()}

    @property
    def close(self) -> typing.Dict[AssetPair,Decimal]:
        return {p: m.close for p, m in self.models.items()}

    @property
    def high(self)-> typing.Dict[AssetPair,Decimal]:
        return {p: m.high for p, m in self.models.items()}

    @property
    def low(self)-> typing.Dict[AssetPair,Decimal]:
        return {p: m.low for p, m in self.models.items()}

    @property
    def volume(self)-> typing.Dict[AssetPair,Decimal]:
        return {p: m.volume for p, m in self.models.items()}

    def _update(self, ohlc_update: OHLCUpdate):
        append_data = ohlc_update.to_tidfrow()

        # updating  our dataframe on network message recv
        for i in append_data.index:
            self.model[i] = append_data[i]
        # TODO : properly: set index to value, not append !!
        # self.model.append(append_data)

        # to propagate updates (using full data !)
        if hasattr(self, 'datamodel'):
            print("Updating datamodel!")
            self.datamodel(self.model.dataframe)

        # for p in self._plots:
        #     p(self.model.dataframe)  # update existing plotS
            # with the aggregated data -> all stitching must have been done before.
            # TODO : figure update optimization : stitch on the fly in the figure...

    def callback(self, user_cb):
        """ a decorator to decorate a pydef be called asynchronously by an update of OHLC data """
        # design to allow wrapper based on user_cb nature (coroutine, pydef, etc.)
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        # TODO : should we throttle the callback to respect timeframe (and not get spammed by each message) ?

        wrp = wrapper(user_cb)

        # we add a callback for this ohlc request data (relying on the wsclient to not store callbacks here)
        # self.wsclient.loop.create_task(  # TODO : create task or directly run_until_complete ?
        #     # subscribe
        #     self.wsclient.ohlc(pairs=[self.pair], callback=wrp)
        # )
        # Note the wsclient is assumed optimized :
        # the channel we already subscribe to will not need to be subscribed again...

        return wrp

    async def __call__(self, restclient: RestClient):
        """
        This is a call mutating this object after async rest data retrieval.
        """

        old_limit = datetime.now(tz=timezone.utc) - self.timeframe.to_timedelta()
        newmodels = dict()
        for p, m in self.models.items():
            if self.model.last < old_limit:  # last data before old_limit : update required

                new_ohlc = (await self.restclient.ohlc(pair=p, interval=self.timeframe))

                if new_ohlc:  # TODO : betterhandling of errors via exceptions...
                    newmodels[p] = m.stitch(new_ohlc)

        return self

    def __repr__(self):
        return f"<OHLC {self.timeframe} {self.models.keys()}>"

    def __str__(self):
        return f"OHLC {self.timeframe} {self.models.keys()}"

    # TODO : maybe we need something to express the value of the asset relative to the fees
    #  => nothing change while < fees, and then it s step by step *2, *3, etc.
    #  Ref : look for "turtle system" on investopedia. but might belong in another package...

    def __getitem__(self, pair: AssetPair):
        return self.models[pair]

    def __iter__(self):
        # Ref : https://thispointer.com/pandas-6-different-ways-to-iterate-over-rows-in-a-dataframe-update-while-iterating-row-by-row/

        # TODO : iterate through the *past* in parallel on all pairs... (in usual time order)
        df = pd.concat([ohlc.dataframe for ohlc in self.models.values()], axis=1, keys=self.models.keys())
        for ts, s in df.iterrows():  # TODO : somehow merge with / reuse OHLCModel __iter__()
            yield { idx: OHLCValue(datetime=ts, **s[idx]) for idx in s.index.levels[0]}

    async def __aiter__(self):
        # TODO : this is were we leverage our websocket implementation
        # forwarding every update to the user (and also using it internally to update the model,
        # waiting for the next (user-triggered) rest request...

        async for ohlc_update in ohlc(pairs=[k for k in self.models.keys()], interval=self.timeframe.value, restclient=self.restclient):

            # TODO : decides if this update means the previous one is final (we cannot do better until we synchronize client and server time...)
            # TODO : store this update until next iteration
            # TODO : update internal model

            yield ohlc_update

    def __len__(self):
        return max(len(m) for m in self.models.values())
        
    # def plot(self):  # Note : doc is needed for updates
    #     """ Multple plots in one column, since all have the xaxis in common."""
    #
    #     if not hasattr(self, "datamodel"):
    #
    #         # TODO : proper fix : shouldnt happen in the first place...
    #         df=self.model.dataframe.drop_duplicates()
    #
    #         self.datamodel = DataModel(df, name="OHLC")
    #     # Note the model should probably be owned by smthg...
    #
    #     # make another plot... (same model -> another source)
    #     ohlcview = ohlc_plot(source=self.datamodel.source)
    #
    #     # TODO : add vwap...
    #
    #     indicator_figs = []
    #     # for i in self.indicators:
    #     #     im = DataModel(data=i, name=)
    #     #     iv = MACDView(model=im, ...)
    #
    #     #     f = i(ohlcp)
    #     #     if isinstance(f, Figure):
    #     #         indicator_figs.append(f)
    #     #     else:
    #     #         # just a plot, it should be already drawn in this OHLCFigure.
    #     #         pass
    #
    #     # TODO : we probably dont need to manage plots and docs here (should be done in server itself....)
    #     # self._plots.append(ohlcp)
    #
    #     return column(ohlcview(plot_height=320, tools='pan, wheel_zoom', toolbar_location="left",
    #                      x_axis_type="datetime", y_axis_location="right",
    #                      sizing_mode="scale_width")) #, *indicator_figs)

    def pivot(self, before: typing.Union[datetime, timedelta], now: datetime= datetime.now(tz=timezone.utc)) -> Pivot:
        if isinstance(before, timedelta):
            before = now - before

        # extract previous timeframe
        previous_tf = self[before: now]
        assert isinstance(previous_tf, OHLCModel)

        # Ref : https://www.easycalculation.com/finance/pivot-points-trading.php
        # Ref : https://www.investopedia.com/terms/p/pivotpoint.asp
        # Pivot Point = (H + C + L) / 3
        pivot = (previous_tf.high + previous_tf.close + previous_tf.low) / 3

        #  R1 = 2 x Pivot - L
        R1 = 2 * pivot - previous_tf.low
        #  S1 = 2 x Pivot - H
        S1 = 2 * pivot - previous_tf.high

        #  R2 = Pivot + ( R1 - S1 )
        R2 = pivot + (R1 - S1)
        #  S2 = Pivot - ( R1 - S1 )
        S2 = pivot - (R1 - S1)

        #  R3 = H + 2 x ( Pivot - L )
        R3 = previous_tf.high + 2 * (pivot - previous_tf.low)
        #  S3 = L - 2 x ( H - Pivot )
        S3 = previous_tf.low - 2 * (previous_tf.high - pivot)

        return Pivot(pivot=pivot, R1=R1, R2=R2, R3=R3, S1=S1, S2=S2, S3=S3)

    def ema(self, length, **plot_kwargs) -> pd.Series:
        # TODO : default values that make sense depending on timeframe...
        emadata = self.model.dataframe.ta.ema(length=length)
        # add ema onto the future plotS
        # self.indicators.append(
        #     lambda p: p.line(name= f"EMA {length}",
        #                      y= f"EMA_{length}",  # we need to pick the correct column name !
        #                      dataframe=self.model.dataframe,
        #                      df_process=lambda df: df.ta.ema(length=length).to_frame(),
        #                      line_width=1, color='navy', **plot_kwargs),
        # )

        return emadata

    def macd(self, fast=3, slow=6, signal=9, **figure_kwargs) -> pd.DataFrame:
        # TODO : default values that make sense depending on timeframe...
        macddata = self.model.dataframe.ta.macd(fast=fast, slow=slow, signal=signal)

        # TODO : parse column headers to deduce columns to plot

        # add macd onto the future plotS
        # self.indicators.append(
        #     lambda p: build_macd(p.doc, p)
        # )

        # macdm = DataModel(macddata, name="MACD", debug=True)
        # macdv = macd_plot(source=macdm.source, fast=fast, slow=slow, signal=signal)
        #     # , plot_height=320, tools='pan, wheel_zoom', toolbar_location="left",
        #     #              x_axis_type="datetime", y_axis_location="right",
        #     #              sizing_mode="scale_width")

        return macddata

    # TODO : Since we have indicators here (totally dependent on ohlc), we probably also want signals...


# async constructor, to enable RAII for this class
# think directed container in time, extracting more data from the now...

# async def ohlc(pair, timeframe: KTimeFrameModel = KTimeFrameModel.one_minute, restclient: RestClient = None, wsclient: WssClient = None, loop=None, valid_time: timedelta = None):
#     ohlc = OHLC(pair=pair, timeframe=timeframe, restclient=restclient,  wsclient=wsclient, loop=loop, valid_time=valid_time)
#     return await ohlc()  # RAII()
#     # TODO : return a proxy instead...


if __name__ == '__main__':

    import asyncio
    from aiokraken.rest.client import RestClient
    from aiokraken.rest.api import Server

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    from aiokraken.domain.pairs import AssetPairs

    async def retrieve_pairs(pairs):
        return await AssetPairs.retrieve(pairs=pairs)

    ap = asyncio.run(retrieve_pairs(["XBT/EUR", "ETH/EUR"]))

    ohlc_1m = asyncio.run(OHLC.retrieve(pairs=ap, timeframe=KTimeFrameModel.one_minute, restclient=rest))

    for k in ohlc_1m:
        print(f" - {k}")

    async def update_loop():
        async for k in ohlc_1m:
            print(f" - {k}")

    asyncio.run(update_loop())

    #
    # async def ohlc_update_watcher():
    #
    #     ohlc_1m.callback(ws_update)
    #
    #     # # Here we register and retrieve an indicator on ohlc data.
    #     # # It will be automagically updated when we update ohlc.
    #     emas_1m = ohlc_1m.ema(length=12, name="EMA_12")
    #     # # Note these two should merge...
    #     ohlc_1m.ema(length=26, name="EMA_26")
    #
    #     # assert len(ohlc_1m) == 720, f"from: {ohlc_1m.begin} to: {ohlc_1m.end} -> {len(ohlc_1m)} values"
    #     # ema has been updated
    #     # assert len(emas_1m) == 720, f"EMA: {len(emas_1m)} values"
    #
    #     print("Waiting 6 more minute to attempt retrieving more ohlc data - via websockets - and stitch them...")
    #     for mins in range(1, 2):  # 6):
    #         await asyncio.sleep(60)  # need await to not block other async tasks
    #         print(f" - {ohlc_1m.model[:-1]}")
    #
    #     await ohlc_1m(restclient=rest)
    #
    #     # assert len(ohlc_1m) == 727, f"from: {ohlc_1m.begin} to: {ohlc_1m.end} -> {len(ohlc_1m)} values"
    #     # ema has been updated
    #     # assert len(emas_1m) == 727, f"EMA: {len(emas_1m)} values"
    #
    #     # to generate a report at this time.
    #     # output_file(f"{ohlc_1m.pair}_{ohlc_1m.timeframe}.html", mode='inline')
    #     # save(ohlc_1m.plot())
    #
    # # TODO : origin server example with fake data... => better interactive debug of this module and dependencies.
    # # Corollary : use types to ensure OHLC interface via mypy, as much as possible...
    #
    # def test_page(doc):
    #
    #     doc.add_root(ohlc_1m.plot())
    #
    # async def main():
    #
    #     from livebokeh.monosrv import monosrv
    #     # bg async task...
    #     asyncio.create_task(ohlc_update_watcher())
    #
    #     await monosrv({'/': test_page})
    #
    # try:
    #     loop.run_until_complete(main())
    # except KeyboardInterrupt:
    #     print("Exiting...")

