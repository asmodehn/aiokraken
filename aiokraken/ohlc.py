import asyncio
from collections import namedtuple
from datetime import timedelta, datetime, timezone

import typing
import pandas as pd
from aiokraken.model.assetpair import AssetPair

from aiokraken.model.indicator import Indicator, EMA_params

from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.model.ohlc import OHLC as OHLCModel
from aiokraken.model.indicator import ema, EMA as EMAModel
from collections.abc import Mapping

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


Pivot = namedtuple("Pivot", ["pivot", "R1", "R2", "R3", "S1", "S2", "S3"])


class OHLC:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the time axis... probably via the callable / iterator protocols
        It is also encapsulating the timeframe concept, and therefore should behave like a directed container
        on the time *interval* axis (nagivating between timeframes), probably via mapping protocol...
    """
    pair: AssetPair
    model: OHLCModel
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    indicators: typing.Dict[str, Indicator]

    def __init__(self, pair, timeframe: KTimeFrameModel = KTimeFrameModel.one_minute, restclient: RestClient = None, valid_time: timedelta = None):
        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid
        self.pair = pair
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
    def open(self):
        return self.model.open

    @property
    def close(self):
        return self.model.close

    @property
    def high(self):
        return self.model.high

    @property
    def low(self):
        return self.model.low

    @property
    def volume(self):
        return self.model.volume

    async def __call__(self):
        """
        This is a call mutating this object. GOAL : updating OHLC out of the view of the user
        (contained datastructures change by themselves, from REST calls of websockets callback...)
        """
        new_ohlc = (await self.restclient.ohlc(pair=self.pair, interval=self.timeframe)())

        if new_ohlc:
            if self.model:
                self.model = self.model.stitch(new_ohlc)
            else:
                self.model = new_ohlc

        for n, i in self.indicators.items():
            i(self.model)  # updating all indicators from new ohlc data

        return self

    # TODO : howto make display to string / repr ??

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

    def pivot(self, before: typing.Union[datetime,timedelta], now: datetime= datetime.now(tz=timezone.utc)) -> Pivot:
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

    def ema(self, name: str, length: int, offset: int = 0, adjust: bool = False) -> EMA:
        # the self updating object
        ema = EMA(name=name, length=length, offset=offset, adjust=adjust)
        self.indicators['ema'] = ema  # TODO : merge EMA with multiple params in same dataframe.
        if self.model:
            self.indicators['ema'] = ema(self.model)  # Immediately calling on ohlc => TODO : improve design ?
        else:
            self.indicators['ema'] = ema  # call will be done later.\
        return self.indicators['ema']

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

    # Here we register and retrieve an indicator on ohlc data.
    # It will be automagically updated when we update ohlc.
    emas_1m = ohlc_1m.ema(name="EMA_12", length=12)

    async def ohlc_retrieve_nosession():
        global rest, ohlc_1m, emas_1m
        await ohlc_1m()
        for k in ohlc_1m:
            print(f" - {k}")

        # TODO : this should probably be done out of sight...
        #emas_1m = emas_1m(ohlc_1m.model)  # explicit update of indicator for this timeframe
        # TODO ohlc.ema(name="EMA_12", length=12) maybe ??

    loop = asyncio.get_event_loop()

    assert len(ohlc_1m) == 0

    loop.run_until_complete(ohlc_retrieve_nosession())
    assert len(ohlc_1m) == 720, f"from: {ohlc_1m.begin} to: {ohlc_1m.end} -> {len(ohlc_1m)} values"
    # ema has been updated
    assert len(emas_1m) == 720, f"EMA: {len(emas_1m)} values"

    print("Waiting one more minute to attempt retrieving more ohlc data and stitch them...")
    time.sleep(60)
    loop.run_until_complete(ohlc_retrieve_nosession())

    assert len(ohlc_1m) == 721, f"from: {ohlc_1m.begin} to: {ohlc_1m.end} -> {len(ohlc_1m)} values"
    # ema has been updated
    assert len(emas_1m) == 721, f"EMA: {len(emas_1m)} values"

    loop.close()



