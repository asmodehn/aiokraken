"""
Implementing a multiresolution timeindexed dataframe.
this is only useful for OHLCV and therefore it is a special case, for practicalities of implementation
"""
import asyncio
import typing

from aiokraken.model.assetpair import AssetPair

from aiokraken.rest import RestClient
from aiokraken.model.timeframe import KTimeFrameModel
from aiokraken.model.ohlc import OHLC as OHLCModel


class OHLCV:
    """
    Class/Type to represent a multi-resolution OHLC.
    The type represents the complete retrievable ohlc over "all time, ever".
    An instance is a slice of it (on time axis), by default covering now and bit before.
    """

    _model: typing.Dict[KTimeFrameModel, OHLCModel]

    def __init__(self, pair: AssetPair, rest: RestClient=None):
        self.rest = rest if rest is not None else RestClient()
        # Note : the RestClient will take care of managing the asyncio loop
        self.pair = pair

        self._model = dict()

    @property
    def days_15(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.fifteen_days))
        return self._model[KTimeFrameModel.fifteen_days]

    @property
    def days_7(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.seven_days))
        return self._model[KTimeFrameModel.seven_days]

    @property
    def hours_24(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.twenty_four_hours))
        return self._model[KTimeFrameModel.twenty_four_hours]

    @property
    def hours_4(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.four_hours))
        return self._model[KTimeFrameModel.four_hours]

    @property
    def minutes_60(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.sixty_minutes))
        return self._model[KTimeFrameModel.sixty_minutes]

    @property
    def minutes_30(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.thirty_minutes))
        return self._model[KTimeFrameModel.thirty_minutes]

    @property
    def minutes_15(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.fifteen_minutes))
        return self._model[KTimeFrameModel.fifteen_minutes]

    @property
    def minutes_5(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.five_minutes))
        return self._model[KTimeFrameModel.five_minutes]

    @property
    def minute(self):
        # TODO : update only if needed...
        self.rest.loop.run_until_complete(self(interval=KTimeFrameModel.one_minute))
        return self._model[KTimeFrameModel.one_minute]

    async def __call__(self, interval: KTimeFrameModel = KTimeFrameModel.fifteen_days,):

        new_ohlc = await self.rest.ohlc(pair=self.pair, interval=interval)

        self._model.setdefault(interval, new_ohlc)
        if interval in self._model:
            self._model[interval].stitch(new_ohlc)

        return self

    # TODO : extend to provide more ohlcv dataframes than the strict kraken API (via resampling from public trades history)


if __name__ == '__main__':

    from aiokraken.domain.pairs import AssetPairs
    XBTEUR = AssetPairs(["XBT/EUR"])

    for p in XBTEUR.values():
        ohlcv = OHLCV(pair=p)

        print(ohlcv.days_15)

        print(ohlcv.minutes_5)




