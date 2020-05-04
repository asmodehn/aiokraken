""" What the user has """
from datetime import datetime, timedelta

import typing
from decimal import Decimal
from types import MappingProxyType

from aiokraken.websockets.client import WssClient

from aiokraken.rest import RestClient


import asyncio
from aiokraken.rest.client import RestClient
from aiokraken.rest.api import Server
from aiokraken.config import load_api_keyfile
from framable import FramableMeta
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
        cls._assets = await rest.retrieve_assets(assets=assets)
        return cls._assets

    _assets: typing.ClassVar[AssetsMapping]

    _proxy: MappingProxyType

    _ledgers: LedgerFrame = None

    def __new__(cls, rest: RestClient=None, assets = None):
        if not hasattr(cls, "_assets"):
            # on first instance, trigger the classwide retrieval
            asyncio.run(cls.retrieve(rest=rest))

        return super(Assets, cls).__new__(cls)

    def __init__(self, rest: RestClient=None, assets = None):
        self._proxy = MappingProxyType({n: d for n, d in self._assets.items() if n in assets or d.altname in assets})

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

    def __getattr__(self, item):  # to delegate copy(), geT(), items(), keys(), values() to mappingproxy
        return getattr(self._proxy, item)

    async def balance(self, rest: RestClient):
        b = await rest.balance()
        return {a: b[a] if a in b else b[ad.altname]
                for a, ad in self.items()
                if a in b or ad.altname in b
                }  # TODO : balance type/namedtuple ?

    # TODO : maybe an access via getitem instead, indexing over time ??
    async def ledger(self, rest: RestClient, start: datetime =None, stop: datetime = None,):
        if rest is not None and (self._ledgers is None or start < self._ledgers.begin or stop > self._ledgers.end):
            # we retrieve all matching ledgerinfos... lazy on times ! # TODO : improve requesting only on unknown times
            ledgerinfos, count = await rest.ledgers(asset=[v for v in self.values()], start=start, end=stop, offset=0)

            # loop until we get *everything*
            # Note : if this is too much, leverage local storage (TODO ! - in relation with time... assume past data doesnt change)
            #  or refine filters (time, etc.)
            while len(ledgerinfos) < count:
                # Note : here we recurse only one time. we need to recurse to respect ratelimit...
                more_ledgers, count = await rest.ledgers(asset=[v for v in self.values()], start=start, end=stop, offset=len(ledgerinfos))
                ledgerinfos.update(more_ledgers)

            ledgers = ledgerframe(ledger_as_dict=ledgerinfos)
            if ledgers:
                self._ledgers = ledgers.value
            else:
                raise RuntimeError("Something went wrong")

        # we keep aggregating in place on the same object
        return self._ledgers


    async def trades(self):
        # TODO : this is just an access point for hte trades module (for private trades)...
        raise NotImplementedError


if __name__ == '__main__':

    # late client (private session) initialization
    keystruct = load_api_keyfile()

    # Client can be global: there is only one.
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    EUR_XBT_XTZ = Assets(rest=rest, assets=["EUR", "XBT", "XTZ"])

    # now we are talking about EUR or XBT or XTZ...

    print(EUR_XBT_XTZ)

    async def balance():
        print(await EUR_XBT_XTZ.balance(rest=rest))


    async def ledgers():
        now = datetime.now()
        print(await EUR_XBT_XTZ.ledger(rest=rest, start= now - timedelta(weeks=1), stop= now))

    asyncio.run(balance())

    asyncio.run(ledgers())
























