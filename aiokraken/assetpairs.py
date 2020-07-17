""" What the market is.

These are mostly (all?) public data.
"""

import asyncio
from datetime import datetime

import typing
from decimal import Decimal
from types import MappingProxyType

from aiokraken.utils import get_kraken_logger

from aiokraken.model.assetpair import AssetPair

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.config import load_api_keyfile

from aiokraken.rest import RestClient, Server
from aiokraken.rest.assetpairs import AssetPairs as AssetPairsMapping
from aiokraken.model.ohlc import OHLC

LOGGER = get_kraken_logger(__name__)


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

    _proxy: MappingProxyType

    def __init__(self, pairs: AssetPairsMapping, filter: typing.Optional[typing.List[str]] = None):
        # Note how the keys use the wsname (more consistent / standard naming than kraken's REST names)
        for p, v in pairs.items():
            if v.wsname is None:
                LOGGER.warning(f"AssetPair {p} IGNORED, no websocket name available.")

        # Note : This will eliminate darkpools as they dont have websocket names just yet
        # To play with darkpools, use the rest subpackage directly via aiokraken.rest
        if filter is not None:
            self._proxy = MappingProxyType({d.wsname: d for n, d in pairs.items() if d.wsname is not None and
                                            (n in filter or
                                            d.altname in filter or
                                            d.wsname in filter)})
        else:
            self._proxy = MappingProxyType({d.wsname: d for n, d in pairs.items() if d.wsname is not None})

    def __repr__(self):
        return repr(self._proxy)

    def __str__(self):
        return str(self._proxy)

    def __getitem__(self, item):
        if item in self._proxy.keys():
            return self._proxy[item]
        else:
            for v in self._proxy.values():
                if item == v.restname or item == v.altname:
                    return v
            raise KeyError(f"{item} not found")

    def __iter__(self):
        """ Iterating on values() to keep 1-1 relationship """
        return iter(self._proxy.values())

    def __contains__(self, item):
        if item in self._proxy.keys():
            return True
        else:
            for v in self._proxy.values():
                if item== v.restname or item == v.altname:
                    return True
            return False

    def __len__(self):
        return len(self._proxy)

    def keys(self):
        return self._proxy.keys()

    def values(self):
        return self._proxy.values()

    def items(self):
        return self._proxy.items()

    # to still be able to specifically access via restname when needed
    def rest(self):
        return MappingProxyType({d.restname: d for n, d in self._proxy.items()})

    async def ticker(self, rest: RestClient = None):
        rest = rest if rest is not None else RestClient()
        t = await rest.ticker(pairs=[k.restname for k in self.values()])
        return {pd.wsname: t[pd.restname]
                for p, pd in self.items()
                if pd.restname in t
                }

    def trades(self, rest: RestClient = None, start: datetime = None, stop: datetime = None):
        # TODO : this is the PUBLIC trade history on the pair. can also be used by ohlcv() to provide historical data
        # Ref : https://support.kraken.com/hc/en-us/articles/218198197-How-to-pull-all-trade-data-using-the-Kraken-REST-API
        raise NotImplementedError

    def trades_history(self):
        """ the private trade history for the current pairs"""
        raise NotImplementedError

    def ohlcv(self, rest: RestClient = None, start: datetime = None, stop: datetime = None): # similar to ledgers for assets
        # late import for convenience function
        from aiokraken.domain.ohlcv import OHLCV

        # deduce tfl from start & stop
        if start > stop:
            opt_tf = (start - stop) / 720
        else:
            opt_tf = (stop - start) / 720

        for tf in KTimeFrameModel:
            if tf > opt_tf:
                break
        # if not found the timeframe will be the largest possible
        return getattr(OHLCV, tf.name)(pairs=[p for p in self.values()], rest=rest)


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
























