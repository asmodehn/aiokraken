import asyncio
import dataclasses
from collections.abc import Mapping

import typing
from datetime import datetime, timezone, timedelta

import dpcontracts
import timecontrol

from aiokraken.config import load_persist
from aiokraken.utils import get_kraken_logger
from aiokraken.utils.filter import Filter
from aiokraken.rest.client import RestClient
from aiokraken.model.asset import Asset

LOGGER = get_kraken_logger(__name__)


class Assets(Mapping):
    """
    Represents Assets.
    Both the one we want to query from the exchange (via filter)
    and the one that we already know about (via impl)
    """
    filter: Filter
    request: typing.Coroutine
    impl: typing.Dict[str, Asset]
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    def __init__(self, f: Filter = None, restclient: RestClient = None, valid_time: timedelta = None):
        self.filter = Filter(blacklist=[]) if f is None else f
        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid
        self.request = self.restclient.assets(assets=self.filter.whitelist) if self.filter.whitelist else self.restclient.assets()

    async def __call__(self, f: Filter = None):  # TODO : add WSSClient to subscribe to get updated
        """
        This is supposed to be called by the Client.
        Direct usage is possible, but wont benefit from client optimizations.
        :return:
        """
        if f:
            # Creating a new instance (immutability semantics) but accumulating the filter
            assets = Assets(f=self.filter + f, restclient=self.restclient)

            # forwarding the call to the new instance.
            return await assets()
        else:

            if self.validtime is None or datetime.now() > self.updated + self.validtime:
                # TODO : check compatibility between request underlimiter and validtime...
                # result not valid any longer -> new request needed
                self.impl = await self.request()
                self.updated = datetime.now(tz=timezone.utc)

            # in any case
            return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if (key in self.filter.whitelist) or self.filter.default:
            return self.impl[key]  # TODO : handled key not in impl case...
        else:
            raise KeyError(f"{key} is a blacklisted Asset and is not accessible.")

    def __iter__(self):
        return iter(self.impl.keys())

    def __len__(self):
        return len(self.impl)

    @dpcontracts.require("Both Assets needs to use the same client", lambda args: args.self.restclient == args.other.restclient)
    def __add__(self, other):
        new = Assets(f=self.filter + other.filter, restclient=self.restclient)  # aggregating filters
        new.impl = self.impl.update(other.impl)  # aggregating results
        return new  # immutable behavior...

    # TODO : maybe extract a partial map proxy pattern from similar classes... might be useful given REST API usual structures.


if __name__ == '__main__':
    # from timecontrol.control import Control
    # from timecontrol.overlimiter import OverLimiter
    #
    # @Control()
    # @OverLimiter(period=10)
    async def assets_retrieve_nosession():
        assets = Assets()
        await assets()  # Optional from the moment we have Local storage
        for k, p in assets.items():
            print(f" - {k}: {p}")


    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()




