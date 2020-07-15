"""
Implementing a multiresolution timeindexed dataframe.
this is only useful for OHLCV and therefore it is a special case, for practicalities of implementation
"""
import asyncio
import functools
import typing
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import bokeh.layouts
import pandas
import wrapt
from aiokraken.model.assetpair import AssetPair

from bokeh.io import output_file
from bokeh.models import CustomJS, LayoutDOM

from aiokraken.domain.assetpairs import AssetPairs

from aiokraken.rest import RestClient, Server
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.model.ohlc import OHLC as OHLCModel, OHLCValue
from aiokraken.websockets.publicapi import ohlc


class OHLCV:
    """
    Class/Type to represent a multi-resolution OHLC.
    The type represents the complete retrievable ohlc over "all time, ever".
    An instance is a slice of it (on time axis), by default covering now and "a bit" (720 intervals) before.
    """

    # layout: bokeh.layouts.LayoutDOM

    models: typing.Dict[AssetPair, OHLCModel]
    # updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    # validtime: timedelta

    @classmethod
    async def one_minute(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        proper_pairs = await rest.retrieve_assetpairs()
        pairs = [p if isinstance(p, AssetPair) else proper_pairs[p] for p in pairs]

        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.one_minute) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    @classmethod
    async def five_minutes(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        # TODO : validate the pairs using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.five_minutes) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    @classmethod
    async def fifteen_minutes(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        # TODO : validate the pairs using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.fifteen_minutes) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    @classmethod
    async def thirty_minutes(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        # TODO : validate the pairs using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.thirty_minutes) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    half_an_hour = thirty_minutes

    @classmethod
    async def sixty_minutes(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        # TODO : validate the pairs using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.sixty_minutes) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    one_hour = sixty_minutes

    @classmethod
    async def four_hours(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        # TODO : validate the pairs using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.four_hours) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    @classmethod
    async def one_day(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        proper_pairs = await rest.retrieve_assetpairs()
        pairs = [p if isinstance(p, AssetPair) else proper_pairs[p] for p in pairs]

        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.one_day) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    twenty_four_hours = one_day

    @classmethod
    async def seven_days(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        # TODO : validate the pairs using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.seven_days) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels ,rest=rest, loop=loop)

    @classmethod
    async def fifteen_days(cls, pairs: AssetPairs, rest: RestClient, loop=None):
        # TODO : validate the pairs using the rest client pair = await self.restclient.validate_pair(pair=self.pair)
        ohlcmodels = {p: await rest.ohlc(pair=p, interval=KTimeFrameModel.fifteen_days) for p in pairs}
        return OHLCV(pair_ohlcmodels=ohlcmodels, rest=rest, loop=loop)

    # TODO : get rid of async on initialization.
    #  HOW : provide storage, and upon initialization, retrieve data from storage.
    #  IMPLIES : we must allow for an "empty" instance to be created, and be updated afterwards.
    #  Note : Not really useful until cold data storage is available... in the meantime, it is just a minor annoyance.
    def __init__(self,  pair_ohlcmodels: typing.Dict[AssetPair, OHLCModel], rest: RestClient, loop = None):

        self.rest = rest if rest is not None else RestClient()

        self.loop = loop if loop is not None else asyncio.get_event_loop()   # TODO : use restclient loop ??

        # TODO : get rid of these before : we are in ONE process, ONE thread => one client and one loop.

        self.models = pair_ohlcmodels

        # self._layouts = list()

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

    @property
    def timeframe(self) -> typing.Dict[AssetPair, KTimeFrameModel]:
        return {p: m.timeframe for p, m in self.models.items()}

    def __repr__(self):
        return f"<OHLC {self.models.keys()} from {self.begin} to {self.end}>"

    def __str__(self):
        return f"OHLC {self.models.keys()} from {self.begin} to {self.end}"

    async def __call__(self, restclient: RestClient):
        """
        This is a call mutating this object after async rest data retrieval.
        """
        newmodels = dict()
        for p, m in self.models.items():
            old_limit = datetime.now(tz=timezone.utc) - m.timeframe
            if m.last < old_limit:  # last data before old_limit : update required

                new_ohlc = (await self.rest.ohlc(pair=p, interval=m.timeframe))

                if new_ohlc:  # TODO : betterhandling of errors via exceptions...
                    newmodels[p] = m.stitch(new_ohlc)

        return self

    # TODO : maybe we need something to express the value of the asset relative to the fees
    #  => nothing change while < fees, and then it s step by step *2, *3, etc.
    #  Ref : look for "turtle system" on investopedia. but might belong in another package...

    def __getitem__(self, item: typing.Union[str, AssetPair,
                                             typing.List[typing.Union[str, AssetPair]],
                                             datetime, timedelta, slice]):
        # converting str to Assetpair
        if isinstance(item, str):
            item = self.rest._assetpairs[item]
        # TODO : review acesspair access after restclient overhaul to drop the class and have only one instance...
        if isinstance(item, AssetPair):
            return self.models[item]  # the usual item access

        # otherwise container behavior on pairs
        elif isinstance(item, list):
            plst = [p if isinstance(p, AssetPair) else self.rest._assetpairs[p] for p in item]
            # container style (over pairs)
            return OHLCV(pair_ohlcmodels={p: m for p, m in self.models.items() if p in plst},rest=self.rest, loop=self.loop)

        # otherwise container behavior over timeintervals, handled by model implementation
        else:
            if isinstance(item, slice) or isinstance(item, datetime) or isinstance(item, timedelta):
                return OHLCV(pair_ohlcmodels={p: m[item] for p, m in self.models.items()}, rest=self.rest, loop=self.loop)
            else:
                raise KeyError(f"{item} is not recognized as an OHLCV key")

    def __contains__(self, item: typing.Union[str,AssetPair]):
        # normalize pair string
        if isinstance(item, str):
            item = self.rest._assetpairs[item].wsname
        # Checking contenance without invoking iterator
        for k in self.models.keys():
            if item == k.wsname or item == k.restname or item == k.altname:
                return True
        else:
            return False

    def __iter__(self):
        # Ref : https://thispointer.com/pandas-6-different-ways-to-iterate-over-rows-in-a-dataframe-update-while-iterating-row-by-row/

        # TODO : iterate through the *past* in parallel on all pairs... (in usual time order)
        df = pandas.concat([ohlc.dataframe for ohlc in self.models.values()], axis=1, keys=self.models.keys())
        for ts, s in df.iterrows():  # TODO : somehow merge with / reuse OHLCModel __iter__()
            yield {idx: OHLCValue(datetime=ts, **s[idx]) for idx in s.index.levels[0]}

    async def __aiter__(self):
        # TODO : this is were we leverage our websocket implementation
        # forwarding every update to the user (and also using it internally to update the model,
        # waiting for the next (user-triggered) rest request...

        # Using minimal timeframe of all for this update
        async for ohlc_update in ohlc(pairs=[k for k in self.models.keys()], interval=min(tf.value for tf in self.timeframe.values()),
                                      restclient=self.rest):
            # TODO : decides if this update means the previous one is final (we cannot do better until we synchronize client and server time...)
            # TODO : store this update until next iteration
            # TODO : update internal model

            yield ohlc_update

    def __len__(self):
        return max(len(m) for m in self.models.values())

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

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    from aiokraken.domain.assetpairs import AssetPairs

    async def retrieve_pairs(pairs):
        return await AssetPairs.retrieve(pairs=pairs)

    ap = asyncio.run(retrieve_pairs(["XBT/EUR", "ETH/EUR"]))

    ohlc_1m = asyncio.run(OHLCV.one_minute(pairs=ap, rest=rest))

    for k in ohlc_1m:
        print(f" - {k}")

    async def update_loop():
        async for k in ohlc_1m:
            print(f" - {k}")

    asyncio.run(update_loop())