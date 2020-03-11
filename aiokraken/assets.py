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
    _filter: Filter
    impl: typing.Dict[str, Asset]
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    def __init__(self, restclient: RestClient = None, valid_time: timedelta = None):
        self._filter = Filter(blacklist=[])
        self.restclient = restclient or RestClient()  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid
        self.impl = dict()

    def filter(self,  whitelist=None, blacklist=None, default_allow = True):
        """
        interactive filtering of the instance
        :return:
        """
        f = Filter(whitelist=whitelist, blacklist=blacklist, default_allow=default_allow)
        self._filter = self._filter + f

        # immediately apply blacklist to content
        self.impl = {k: v for k, v in self.impl.items() if k not in blacklist}

    # Note : here we use imperative style, and calling will update contained data (ie mutating...)
    async def __call__(self, force = False):  # TODO : add WSSClient to subscribe to get updated
        if force or self.validtime is None or datetime.now() > self.updated + self.validtime:
            # TODO : check compatibility between request underlimiter and validtime...
            # result not valid any longer -> new request needed

            if self._filter.whitelist:
                self.impl = await self.restclient.assets(assets=self._filter.whitelist)
            else:
                self.impl = await self.restclient.assets()
            self.updated = datetime.now(tz=timezone.utc)

        # in any case
        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if (key in self._filter.whitelist) or self._filter.default:
            return self.impl[key]  # TODO : handled key not in impl case...
        else:
            raise KeyError(f"{key} is a blacklisted Asset and is not accessible.")

    def __iter__(self):
        return iter(self.impl.keys())

    def __len__(self):
        return len(self.impl)
    #
    # @dpcontracts.require("Both Assets needs to use the same client", lambda args: args.self.restclient == args.other.restclient)
    # def __add__(self, other):
    #     new = Assets(f=self.filter + other.filter, restclient=self.restclient)  # aggregating filters
    #     new.impl = self.impl.update(other.impl)  # aggregating results
    #     return new  # immutable behavior...

    # TODO : maybe extract a partial map proxy pattern from similar classes... might be useful given REST API usual structures.


async def assets(restclient: RestClient):
    # async constructor, to enable RAII for this class - think directed container in time, extracting more data from the now...
    a = Assets(restclient=restclient)
    return await a()  # RAII()
    # TODO : return a proxy instead...


if __name__ == '__main__':
    import time
    # from timecontrol.control import Control
    # from timecontrol.overlimiter import OverLimiter

    assets = Assets()

    # @Control()
    # @OverLimiter(period=10)
    async def assets_retrieve_nosession():
        await assets()  # Optional from the moment we have Local storage
        for k, p in assets.items():
            print(f" - {k}: {p}")


    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())
    time.sleep(1)

    loop.run_until_complete(assets_retrieve_nosession())


    loop.close()




