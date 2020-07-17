""" What the user has """
from datetime import datetime, timedelta

import typing
from decimal import Decimal
from types import MappingProxyType

from aiokraken.rest import RestClient


import asyncio
from aiokraken.rest.client import RestClient
from aiokraken.rest.api import Server
from aiokraken.config import load_api_keyfile
from aiokraken.model.ledgerframe import LedgerFrame, ledgerframe
from aiokraken.rest.assets import Assets as AssetsMapping


class Assets:
    """
    Encapsulating dataclass implementation of asset data,
    and providing convenient functionalities.

    The type is the complete list of Asset (potential knowable on retrieval)
    The instance is a subset of it (the ones we already retrieved and know about)
    """
    @classmethod
    async def retrieve(cls, rest: RestClient = None, assets: typing.List[str] = None):
        rest = RestClient() if rest is None else rest
        # retrieve all and filter later, since str is likely not the kraken name...
        assetsmap = await rest.retrieve_assets()
        return cls(assets=assetsmap, filter=assets)

    _proxy: MappingProxyType

    def __init__(self, assets: AssetsMapping, filter=None):
        if filter is not None:
            self._proxy = MappingProxyType({n: d
                                            for n, d in assets.items()
                                            if n in filter or d.altname in filter
                                            })
        else:
            self._proxy = MappingProxyType(assets)

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

    async def balance(self, rest: RestClient):
        b = await rest.balance()
        return {a: b[a] if a in b else b[ad.altname]
                for a, ad in self.items()
                if a in b or ad.altname in b
                }  # TODO : balance type/namedtuple ?

    # TODO : maybe an access via getitem instead, indexing over time ??
    async def ledger(self, rest: RestClient, start: datetime =None, stop: datetime = None,):
        from aiokraken.domain.ledgers import Ledger

        return await Ledger.retrieve(start=start, end=stop, assets=[v for v in self.values()], rest=rest)

    async def trades(self):
        # TODO : this is just an access point for hte trades module (for private trades)...
        raise NotImplementedError


if __name__ == '__main__':

    # late client (private session) initialization
    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    async def retrieval(assets):
        return await Assets.retrieve(rest = rest, assets=assets)

    EUR_XBT_XTZ = asyncio.run(retrieval(assets=["EUR", "XBT", "XTZ"]))

    # now we are talking about EUR or XBT or XTZ...

    print(EUR_XBT_XTZ)

    async def balance():
        print(await EUR_XBT_XTZ.balance(rest=rest))

    async def ledgers():
        now = datetime.now()
        print(await EUR_XBT_XTZ.ledger(rest=rest, start=now - timedelta(weeks=1), stop=now))

    asyncio.run(balance())

    asyncio.run(ledgers())


