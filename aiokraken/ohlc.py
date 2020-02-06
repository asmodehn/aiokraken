import asyncio
from datetime import timedelta, datetime

import typing

from aiokraken import RestClient
from aiokraken.model.indicator import Indicator
from aiokraken.rest import Server


from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.model.ohlc import OHLC as OHLCModel
from aiokraken.timeframe import TimeFrame
from collections.abc import Mapping

from aiokraken.utils.filter import Filter
# from aiokraken.tradesignal import TradeSignal


class OHLC:
    """ Note : This is the monad / mutable state, providing an "imperative" interface to immutable data.
        There fore it should act as a container, on the time axis... probably via the callable / iterator protocols
        It is also encapsulating the timeframe concept, and therefore should behave like a directed container
        on the time *interval* axis (nagivating between timeframes), probably via mapping protocol...
    """

    impl: typing.Dict[KTimeFrameModel, OHLCModel]
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    def __init__(self, pair,  restclient: RestClient = None, valid_time: timedelta = None):
        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid
        self.pair = pair
        self.impl = dict()

    @property
    def begin(self) -> datetime:
        return min(m.begin for tf, m in self.impl.items())

    @property
    def end(self) -> datetime:
        return max(m.end for tf, m in self.impl.items())

    @property
    def open(self):
        return {tf: m.open for tf, m in self.impl.items()}

    @property
    def close(self):
        return {tf: m.close for tf, m in self.impl.items()}

    @property
    def high(self):
        return max(m.high for tf, m in self.impl.items())

    @property
    def low(self):
        return min(m.low for tf, m in self.impl.items())

    @property
    def volume(self):
        return {tf: m.volume for tf, m in self.impl.items()}

    async def __call__(self, timeframe: KTimeFrameModel = KTimeFrameModel.one_minute, ):
        """
        """
        new_ohlc = (await self.restclient.ohlc(pair=self.pair, interval=timeframe)())

        if new_ohlc:
            if self.impl.get(timeframe):
                self.impl[timeframe] = self.impl[timeframe].stitch(new_ohlc)
            else:
                self.impl[timeframe] = new_ohlc

        return self
    #
    # # TODO : maybe tradesignals should be attribute of market and not OHLC...
    # def signal(self, **kwargs):
    #     self.signals.setdefault('ohlc', TradeSignal(self.impl))
    #     return self.signals.get('ohlc')
    #
    # def ema(self, **kwargs):
    #     self.signals.setdefault('ema', TradeSignal(self.impl.ema(**kwargs)))
    #     return self.signals.get('ema')

    # TODO : howto make display to string / repr ??

    # Getitem should be used for multi-precision time introspection into the OHLC dataframe...
    def __getitem__(self, key: KTimeFrameModel):  # Maybe we can allow differents types here and provide multiple implementations ?
        return self.impl[key]  #TODO : some nicer user syntax for watchnig an interval at a specific resolution...


    # TODO: Iterator should be kept for the comonadic interface to the directed container
    #  ie have a "consumption" semantics of timesteps that we have already looked at
    # => The main program (ie, the user's trading plan) should be the one consuming this if interested.
    # ideally this should be asynchronous, and we must wait until next update is available...
    # OTOH signal provide an asynchronous/callbacky way to react to changes.
    def __iter__(self):  # cf PEP 525 for async iterators
        # Ref : https://thispointer.com/pandas-6-different-ways-to-iterate-over-rows-in-a-dataframe-update-while-iterating-row-by-row/
        return iter(self.impl)

    # Length semantics... TODO
    # Problem: we store with precision semantics at the high level, but human think with duration semantics at first...
    def __len__(self):
        if self.impl:
            return len(self.impl)
        else:
            return 0


if __name__ == '__main__':
    import time

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    # ohlc data can be global (one per market*timeframe only)
    ohlc = OHLC(pair='ETHEUR', restclient=rest)

    async def ohlc_retrieve_nosession():
        global rest, ohlc
        await ohlc(timeframe=KTimeFrameModel.one_minute)
        for k in ohlc[KTimeFrameModel.one_minute]:
            print(f" - {k}")

    loop = asyncio.get_event_loop()

    assert len(ohlc) == 0

    loop.run_until_complete(ohlc_retrieve_nosession())
    assert len(ohlc[KTimeFrameModel.one_minute]) == 720, f"from: {ohlc[KTimeFrameModel.one_minute].begin} to: {ohlc[KTimeFrameModel.one_minute].end} -> {len(ohlc[KTimeFrameModel.one_minute])} values"

    print("Waiting one more minute to attempt retrieving more ohlc data and stitch them...")
    time.sleep(60)
    loop.run_until_complete(ohlc_retrieve_nosession())

    assert len(ohlc[KTimeFrameModel.one_minute]) == 721,  f"from: {ohlc[KTimeFrameModel.one_minute].begin} to: {ohlc[KTimeFrameModel.one_minute].end} -> {len(ohlc[KTimeFrameModel.one_minute])} values"

    loop.close()

