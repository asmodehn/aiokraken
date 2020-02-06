# This is a multi-timeframe indicator.
#  We follow the ohlc implementation, BUT we do not have an async interface,
#  as an indicator depends on ohlc only and is entirely computed locally.
# Therefore we should not provide potential await points, because the inicator would not be consistent with ohlc.
import typing

from aiokraken import OHLC
from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.model.indicator import ema, EMA as EMAModel


class EMA:
    """
    Set of Mutable EMA Dataframes, indexed by timeframe ie precision/resolution.
    """

    impl: typing.Dict[KTimeFrameModel, EMAModel]

    def __init__(self, pair, ema: EMAModel, **instances):  # Note : pair seems useless here. depends on ohlc later. TODO : remove
        # Note we may have differences in implementation between indicators based on time intervals
        # and indicator based on number of offset data points (no matter the frequency)...
        self.pair = pair
        self.impl = instances if instances else dict()  # make sure we recreate a dict everytime...
        self.ema = ema

    def __call__(self, ohlc: OHLC):  # update from ohlc
        for tf in ohlc:
            self.impl.setdefault(tf, self.ema)
            self.impl[tf] = self.impl[tf](ohlc[tf])

        return self  # return mutated self

    def __getitem__(self, item):
        if isinstance(item, KTimeFrameModel):
            # this is a container... allows a different and useful semantics for a slice (on the other dimension)
            #return EMA(pair= self.pair, ema=self.ema, **{ft: ind for ft, ind in self.impl.items() if ft <= item})
            # OR maybe not ?
            return self.impl[item]
        # TODO : handle all these cases with ONE timedataframe call ??
        elif isinstance(item, str):
            # selection of one column only
            return EMA(pair= self.pair, ema=self.ema, **{ft: ind[item].to_frame() for ft, ind in self.impl.items()})
        elif isinstance(item, slice):
            # pick the interval from all timeframes
            return EMA(pair=self.pair, ema=self.ema, **{ft: ind[item] for ft, ind in self.impl.items()})
        return EMA


if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.client import RestClient
    from aiokraken.rest.api import Server

    # Client can be global: there is only one.
    rest = RestClient(server=Server())

    # ohlc data can be global (one per market*timeframe only)
    ohlc = OHLC(pair='ETHEUR', restclient=rest)
    # TODO : better manage pair and timeframe in marketdata itself ??
    emas = EMA(pair='ETHEUR', ema=ema(name="EMA_12", length=12))

    async def ohlc_retrieve_nosession():
        global rest, ohlc
        await ohlc(timeframe=KTimeFrameModel.one_minute)
        for k in ohlc[KTimeFrameModel.one_minute]:
            print(f" - {k}")

        emas(ohlc)  # modified in place


    loop = asyncio.get_event_loop()

    assert len(ohlc) == 0

    loop.run_until_complete(ohlc_retrieve_nosession())
    assert len(ohlc[
                   KTimeFrameModel.one_minute]) == 720, f"from: {ohlc[KTimeFrameModel.one_minute].begin} to: {ohlc[KTimeFrameModel.one_minute].end} -> {len(ohlc[KTimeFrameModel.one_minute])} values"
    # ema has been updated
    assert len(emas[
                   KTimeFrameModel.one_minute]) == 720, f"from: {emas[KTimeFrameModel.one_minute].begin} to: {emas[KTimeFrameModel.one_minute].end} -> {len(emas[KTimeFrameModel.one_minute])} values"

    print("Waiting one more minute to attempt retrieving more ohlc data and stitch them...")
    time.sleep(60)
    loop.run_until_complete(ohlc_retrieve_nosession())

    assert len(ohlc[
                   KTimeFrameModel.one_minute]) == 721, f"from: {ohlc[KTimeFrameModel.one_minute].begin} to: {ohlc[KTimeFrameModel.one_minute].end} -> {len(ohlc[KTimeFrameModel.one_minute])} values"
    # ema has been updated
    assert len(emas[
                   KTimeFrameModel.one_minute]) == 721, f"from: {emas[KTimeFrameModel.one_minute]} to: {emas[KTimeFrameModel.one_minute]} -> {len(emas[KTimeFrameModel.one_minute])} values"

    loop.close()


