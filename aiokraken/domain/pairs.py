""" What the market is.

These are mostly (all?) public data.
"""

import asyncio
from datetime import datetime

import typing
from decimal import Decimal
from types import MappingProxyType

from aiokraken.model.assetpair import AssetPair

from aiokraken.domain.ohlcv import OHLCV

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.config import load_api_keyfile

from aiokraken.rest import RestClient, Server
from aiokraken.rest.assetpairs import AssetPairs as AssetPairsMapping
from aiokraken.model.ohlc import OHLC


class AssetPairs:
    """
    Encapsulating dataclass implementation of asset data,
    and providing convenient functionalities.

    The type is the complete list of Asset (potential knowable on retrieval)
    The instance is a subset of it (the ones we already retrieved and know about)
    """
    @classmethod
    async def retrieve(cls, pairs: typing.List[str] = None, rest: RestClient = None, ):
        rest = RestClient() if rest is None else rest
        # retrieve all assets, since list of str likely not matching kraken names
        assetpairs = await rest.retrieve_assetpairs()
        # then filter on usage
        return cls(pairs=assetpairs, filter=pairs)

    _assetpairs: typing.ClassVar[AssetPairsMapping]

    _proxy: MappingProxyType

    _ohlcvs: typing.Dict[AssetPair, OHLC]

    def __init__(self, pairs: AssetPairsMapping, filter: typing.List[str]):
        self._proxy = MappingProxyType({n: d for n, d in pairs.items() if
                                        n in filter or
                                        d.altname in filter or
                                        d.wsname in filter})

    def __repr__(self):
        return repr(self._proxy)

    def __str__(self):
        return str(self._proxy)

    def __getitem__(self, item):
        return self._proxy[item]

    def __iter__(self):
        return iter(self._proxy)

    def __len__(self):
        return len(self._proxy)

    def keys(self):
        return self._proxy.keys()

    def values(self):
        return self._proxy.values()

    def items(self):
        return self._proxy.items()

    async def ticker(self, rest: RestClient = None):
        rest = rest if rest is not None else RestClient()
        t = await rest.ticker(pairs=[k for k in self.keys()])
        return {p: t[p] if p in t else
                t[pd.altname] if pd.altname in t else
                t[pd.wsname]
                for p, pd in self.items()
                if p in t or pd.altname in t or pd.wsname in t
                }  # TODO : balance type/namedtuple ?

    def trades(self, rest: RestClient = None, start: datetime = None, stop: datetime = None):
        # TODO : this is the PUBLIC trade history on the pair. can also be used by ohlcv() to provide historical data
        # Ref : https://support.kraken.com/hc/en-us/articles/218198197-How-to-pull-all-trade-data-using-the-Kraken-REST-API
        raise NotImplementedError

    def trades_history(self):
        """ the private trade history for the current pairs"""
        raise NotImplementedError

    def ohlcv(self, rest: RestClient = None):  # TODO: , start: datetime = None, stop: datetime = None): ( similar to ledgers for assets )
        return {p: OHLCV(pair=pd, rest=rest) for p, pd in self.items()}


if __name__ == '__main__':

    # Client can be global: there is only one.
    # Most of this information is public.
    rest = RestClient(server=Server())

    async def retrieval(pairs):
        return await AssetPairs.retrieve(pairs=pairs, rest=rest)

    XBTEUR_XTZEUR = asyncio.run(retrieval(["XBT/EUR", "XTZ/EUR"]))

    # now we are talking about XBT/EUR or XTZ/EUR...

    print(XBTEUR_XTZEUR)  # the assetpair/market data

    for p, od in XBTEUR_XTZEUR.ohlcv(rest=rest).items():
        print(p)
        # OHLCV is not async because w might be able to use still valid, previously requested, data
        print(od.minutes_5)

    # Ticker is async because we always have to request the new data...
    async def ticker():
        print(await XBTEUR_XTZEUR.ticker(rest=rest))

    asyncio.run(ticker())
























