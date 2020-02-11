import asyncio
import time
from datetime import timedelta, datetime

import typing
from decimal import Decimal

from aiokraken.rest import RestClient

from collections.abc import Mapping

from aiokraken.utils.filter import Filter


class Balance(Mapping):
    # TODO : Design concept. At this level of the package, the classes are containers for data that can "change"
    #  (in a controlled way : always the same type) because of rest or ws communication, "under the hood",
    #  meaning the user is not aware of it, unless a signal is triggered...

    _filter: Filter
    impl: typing.Dict[str, Decimal]
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    def __init__(self, restclient: RestClient, valid_time: timedelta = None):
        self._filter = Filter(blacklist=[])
        self.restclient = restclient  # we require a restclient here, since all requests are private
        self.validtime = valid_time   # None means always valid
        self.assets = dict()

    def filter(self,  whitelist=None, blacklist=None, default_allow = True):
        """
        interactive filtering of the instance
        :return:
        """
        f = Filter(whitelist=whitelist, blacklist=blacklist, default_allow=default_allow)
        self._filter = self._filter + f

        # immediately apply blacklist to content
        self.impl = {k: v for k, v in self.impl.items() if k not in blacklist}

    async def __call__(self):
        """
        """
        # TODO : meaning of filter here... not showing blacklisted assets ? only retrieving whitelist assets ?
        self.impl = (await self.restclient.balance()())

        # get a partial view of assets locally
        self.assets = {n: a for n, a in self.restclient._assets.items() if n not in self._filter.blacklist}

        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if (key in self._filter.whitelist) or self._filter.default:
            return self.impl[key]  # TODO : handled key not in impl case...
        else:
            raise KeyError(f"{key} is a blacklisted Asset and is not accessible.")

    # TODO : maybe we should keep iter design for time dependent collections (OHLC, timeseries, etc.)
    #     And have key addressing only for time independent collections (index is obvious for humans - not a cryptic timestamp)...
    def __iter__(self):
        return iter(self.impl.keys())

    def __len__(self):
        return len(self.impl)



async def balance(restclient: RestClient):
    # async constructor, to enable RAII for this class - think directed container in time, extracting more data from the now...
    b = Balance(restclient=restclient)
    return await b()  # RAII()
    # TODO : return a proxy instead...


if __name__ == '__main__':
    import time
    import asyncio
    from aiokraken.rest.client import RestClient
    from aiokraken.rest.api import Server
    from aiokraken.config import load_api_keyfile

    keystruct = load_api_keyfile()
    rest = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))
    balance = Balance(restclient=rest)

    async def balance_retrieve_nosession():
        await balance()
        for k, p in balance.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(balance_retrieve_nosession())
    time.sleep(1)

    # If we have access to past trades, we can recover the cost of each asset amount.
    from aiokraken.trades import Trades

    from aiokraken import Markets

    mkts = Markets(restclient=rest)

    async def markets_retrieve_nosession():
        global rest, mkts
        await mkts()

    loop.run_until_complete(markets_retrieve_nosession())

    for n, v in balance.items():
        c = mkts.tradecost(asset=balance.assets.get(n), amount=v)
        print(f"{n}: {v} cost from trades is {c}")
    # REMINDER : This must remain safe for the user : do not create any orders.
    # Rely on integration tests to validate merging of data.

    loop.close()


