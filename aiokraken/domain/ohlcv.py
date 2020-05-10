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
    An instance is a slice of it (on time axis), by default covering now and "a bit" (720 intervals) before.
    """

    _model: typing.Dict[KTimeFrameModel, OHLCModel]

    @classmethod
    async def retrieve(cls, pair: AssetPair, rest: RestClient = None, intervals : typing.List[KTimeFrameModel] = None):

        if rest is None:
            rest = RestClient()

        if intervals is None:
            intervals = [i for i in KTimeFrameModel]

        multitf = dict()

        for i in intervals:
            new_ohlc = await rest.ohlc(pair=pair, interval=i)
            multitf.setdefault(i, new_ohlc)

        return cls(pair=pair, rest=rest, multitf=multitf)

    def __init__(self, pair: AssetPair, rest: RestClient, multitf: typing.Dict[KTimeFrameModel, OHLCModel]):
        self.rest = rest if rest is not None else RestClient()

        self.pair = pair

        self._model = multitf

    @property
    def days_15(self):
        return self._model[KTimeFrameModel.fifteen_days]

    @property
    def days_7(self):
        return self._model[KTimeFrameModel.seven_days]

    @property
    def hours_24(self):
        return self._model[KTimeFrameModel.twenty_four_hours]

    @property
    def hours_4(self):
        return self._model[KTimeFrameModel.four_hours]

    @property
    def minutes_60(self):
        return self._model[KTimeFrameModel.sixty_minutes]

    @property
    def minutes_30(self):
        return self._model[KTimeFrameModel.thirty_minutes]

    @property
    def minutes_15(self):
        return self._model[KTimeFrameModel.fifteen_minutes]

    @property
    def minutes_5(self):
        return self._model[KTimeFrameModel.five_minutes]

    @property
    def minute(self):
        return self._model[KTimeFrameModel.one_minute]

    async def __call__(self, interval: KTimeFrameModel = KTimeFrameModel.fifteen_days,):

        new_ohlc = await self.rest.ohlc(pair=self.pair, interval=interval)

        self._model.setdefault(interval, new_ohlc)
        if interval in self._model:
            self._model[interval].stitch(new_ohlc)

        return self

    def __getitem__(self, item):
        return self._model[item]

    def __iter__(self):
        return iter(self._model)


    def fig(self):
        # TODO : radio buttons to swithh between timeframes...
        pass

    # TODO : extend to provide more ohlcv dataframes than the strict kraken API (via resampling from public trades history)


if __name__ == '__main__':

    from aiokraken.domain.pairs import AssetPairs

    from bokeh.plotting import output_file, save

    async def retrieve_pairs(pairs):
        return await AssetPairs.retrieve(pairs=pairs)

    ap = asyncio.run(retrieve_pairs(["XBT/EUR", "ETH/EUR"]))

    async def retrieve_ohlc(p, timeframe):
        return await OHLCV.retrieve(pair=p, intervals=[timeframe])

    for p in ap:
        ohlcv = asyncio.run(retrieve_ohlc(p, KTimeFrameModel.one_day))
        for tf in ohlcv:
            print(ohlcv[tf])
            f = ohlcv[tf].plot()
            output_file(f"{p}_{tf}.html", mode='inline')
            save(f)

