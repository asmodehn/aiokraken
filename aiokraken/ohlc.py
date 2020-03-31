from __future__ import annotations
import asyncio
import dataclasses
from collections import namedtuple
from datetime import timedelta, datetime, timezone

import typing
from decimal import Decimal

import pandas as pd
import wrapt

from aiokraken.websockets.client import WssClient

from aiokraken.model.assetpair import AssetPair

from aiokraken.model.indicator import Indicator, EMA_params

from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.model.ohlc import OHLC as OHLCModel
from aiokraken.model.indicator import ema, EMA as EMAModel
from aiokraken.websockets.schemas.ohlc import OHLCUpdate
from collections.abc import Mapping

from aiokraken.websockets.decorators import ohlc as ohlc_callback
from aiokraken.utils.filter import Filter
# from aiokraken.tradesignal import TradeSignal

class EMA:
    """ OHLC driven updating EMA"""

    model: EMAModel

    def __init__(self, name:str, length: int, offset: int = 0, adjust: bool = False):
        self.model = ema(name=name, length=length, offset=offset, adjust=adjust)

    def __call__(self, ohlc):
        # updating our encapsulated model
        self.model = self.model(ohlc)
        return self

    def __getitem__(self, item):
        return self.model[item]

    def __len__(self):
        return len(self.model)

    def __mul__(self, other):
        self.model = self.model * other.model  # TODO : better : without modifying self...
        return self


Pivot = namedtuple("Pivot", ["pivot", "R1", "R2", "R3", "S1", "S2", "S3"])


class OHLC:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the time axis... probably via the callable / iterator protocols
        It is also encapsulating the timeframe concept, and therefore should behave like a directed container
        on the time *interval* axis (nagivating between timeframes), probably via mapping protocol...
    """
    pair: AssetPair
    model: typing.Optional[OHLCModel]
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    indicators: typing.Dict[str, EMA]

    def __init__(self, pair, timeframe: KTimeFrameModel = KTimeFrameModel.one_minute, restclient: RestClient = None, wsclient: WssClient = None, loop=None, valid_time: timedelta = None):
        self.pair = pair  # TODO : validate the pair using the rest client pair = await self.restclient.validate_pair(pair=self.pair)

        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...

        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.wsclient = wsclient if wsclient is not None else WssClient(loop=self.loop)
        # defaults to have a websocket client

        self.validtime = valid_time   # None means always valid
        self.timeframe = timeframe
        self.model = None  # Need async call : raii is not doable here...
        self.indicators = dict()

    @property
    def begin(self) -> datetime:
        return self.model.begin

    @property
    def end(self) -> datetime:
        return self.model.end

    @property
    def open(self) -> Decimal:
        return self.model.open

    @property
    def close(self) -> Decimal:
        return self.model.close

    @property
    def high(self)-> Decimal:
        return self.model.high

    @property
    def low(self)-> Decimal:
        return self.model.low

    @property
    def volume(self)-> Decimal:
        return self.model.volume

    # TODO : use the decorator for wss callback here !
    def _update(self, ohlc_update: OHLCUpdate):
        try:
            append_data = ohlc_update.to_tidfrow()
            self.model.append(append_data)
            # TODO : indicators update... and more
        except Exception as e:
            print(e)
            raise  # To immediately explicitely catch it

    def callback(self, user_cb):
        """ a decorator to decorate a pydef be called asynchronously by an update of OHLC data """
        # design to allow wrapper based on user_cb nature (coroutine, pydef, etc.)
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            return wrapped(*args, **kwargs)

        wrp = wrapper(user_cb)

        # we add a callback for this ohlc request data (relying on the wsclient to not store callbacks here)
        self.wsclient.loop.create_task(  # TODO : create task or directly run_until_complete ?
            # subscribe
            self.wsclient.ohlc(pairs=[self.pair], callback=wrp)
        )
        # Note the wsclient is assumed optimized :
        # the channel we already subscribe to will not need to be subscribed again...

        return wrp

    async def __call__(self):
        """
        This is a call mutating this object. GOAL : updating OHLC out of the view of the user
        (contained datastructures change by themselves, from REST calls or websockets callback...)
        """

        if self.model and self.model.last > datetime.now(tz=timezone.utc) - self.timeframe.to_timedelta():
            # no need to update just yet, lets wait a bit
            wait_time = self.timeframe.to_timedelta() - (datetime.now(tz=timezone.utc) - self.model.last)
            await asyncio.sleep(wait_time.total_seconds())

        new_ohlc = (await self.restclient.ohlc(pair=self.pair, interval=self.timeframe))

        if new_ohlc:
            if self.model:
                self.model = self.model.stitch(new_ohlc)
            else:
                self.model = new_ohlc

        for n, i in self.indicators.items():
            i(self.model)  # updating all indicators from new ohlc data

        # we got a response from REST, we can now subscribe to our topic via the websocket connection

        if self.wsclient is not None:
            # TODO : prevent redundant subscription ?
            await self.wsclient.ohlc(pairs=[self.pair], callback=self._update)

        return self

    def __repr__(self):
        return f"<OHLC {self.pair} {self.timeframe}>"

    def __str__(self):
        return f"OHLC {self.pair} {self.timeframe}"

    # TODO : maybe we need something to express the value of the asset relative to the fees
    #  => nothing change while < fees, and then it s step by step *2, *3, etc.

    def __getitem__(self, key):  # Maybe we can allow differents types here and provide multiple implementations ?
        return self.model[key]

    # TODO: Iterator should be kept for the comonadic interface to the directed container
    #  ie have a "consumption" semantics of timesteps that we have already looked at
    # => The main program (ie, the user's trading plan) should be the one consuming this if interested.
    # ideally this should be asynchronous, and we must wait until next update is available...
    # OTOH signal provide an asynchronous/callbacky way to react to changes.
    def __iter__(self):  # cf PEP 525 for async iterators
        # Ref : https://thispointer.com/pandas-6-different-ways-to-iterate-over-rows-in-a-dataframe-update-while-iterating-row-by-row/
        return iter(self.model)

    # Length semantics... TODO
    # Problem: we store with precision semantics at the high level, but human think with duration semantics at first...
    def __len__(self):
        if self.model:
            return len(self.model)
        else:
            return 0

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

    def ema(self, name: str, length: int, offset: int = 0, adjust: bool = False) -> OHLC:
        # the self updating object
        ema = EMA(name=name, length=length, offset=offset, adjust=adjust)
        if 'ema' in self.indicators:
            self.indicators['ema'] = self.indicators['ema'] * ema  # merging EMAs in one dataframe !
        else:
            self.indicators['ema'] = ema

        if self.model:  # Immediately calling on ohlc if possible => TODO : improve design ?
            self.indicators['ema'] = self.indicators['ema'](self.model)

        return self  # to allow chaining methods. (no point returning the ema created, it is stored already)

    # TODO : Since we have indicators here (totally dependent on ohlc), we probably also want signals...


# async constructor, to enable RAII for this class
# think directed container in time, extracting more data from the now...

async def ohlc(pair, timeframe: KTimeFrameModel = KTimeFrameModel.one_minute, restclient: RestClient = None,):
    ohlc = OHLC(pair=pair, timeframe=timeframe, restclient=restclient)
    return await ohlc()  # RAII()
    # TODO : return a proxy instead...


if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.client import RestClient
    from aiokraken.rest.api import Server

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    # ohlc data can be global (one per market*timeframe only)
    ohlc_1m = OHLC(pair='ETHEUR', timeframe=KTimeFrameModel.one_minute, restclient=rest)

    loop = asyncio.get_event_loop()

    async def ohlc_update_watcher():
        # we need an async def here to allow "pausing" in the flow (await), and wait for ohlc updates

        # Here we register and retrieve an indicator on ohlc data.
        # It will be automagically updated when we update ohlc.
        emas_1m = ohlc_1m.ema(name="EMA_12", length=12)
        # Note these two should merge...
        ohlc_1m.ema(name="EMA_26", length=26)

        assert len(ohlc_1m) == 0

        await ohlc_1m()
        for k in ohlc_1m:
            print(f" - {k}")

        assert len(ohlc_1m) == 720, f"from: {ohlc_1m.begin} to: {ohlc_1m.end} -> {len(ohlc_1m)} values"
        # ema has been updated
        assert len(emas_1m) == 720, f"EMA: {len(emas_1m)} values"

        print("Waiting 6 more minute to attempt retrieving more ohlc data - via websockets - and stitch them...")
        for mins in range(1, 6):
            await asyncio.sleep(60)  # need await to not block other async tasks
            print(f" - {ohlc_1m.model[:-1]}")

        assert len(ohlc_1m) == 727, f"from: {ohlc_1m.begin} to: {ohlc_1m.end} -> {len(ohlc_1m)} values"
        # ema has been updated
        assert len(emas_1m) == 727, f"EMA: {len(emas_1m)} values"

        # TODO : another REST update should fit with already gathered data

    loop.run_until_complete(ohlc_update_watcher())



