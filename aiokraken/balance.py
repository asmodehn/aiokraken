import asyncio
import time
from datetime import timedelta, datetime

import typing
from decimal import Decimal

from aiokraken.config import load_account_persist
from aiokraken.rest import RestClient, Server

from collections.abc import Mapping

from aiokraken.utils.filter import Filter


class Balance(Mapping):
    # TODO : Design concept. At this level of the package, the classes are containers for data that can "change"
    #  (in a controlled way : always the same type) because of rest or ws communication, "under the hood",
    #  meaning the user is not aware of it, unless a signal is triggered...

    filter: Filter
    request: typing.Coroutine
    impl: typing.Dict[str, Decimal]
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    def __init__(self, restclient: RestClient = None, valid_time: timedelta = None):
        self.filter = Filter(blacklist=[])
        self.restclient = restclient  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid
        self.request = self.restclient.balance()
        # TODO : implement filter by filtering balance view

    async def __call__(self):
        """
        """
        self.impl = (await self.request()).accounts  # TODO : why the extra 'accounts' level ? can we get rid of it somehow ?

        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if (key in self.filter.whitelist) or self.filter.default:
            return self.impl[key]  # TODO : handled key not in impl case...
        else:
            raise KeyError(f"{key} is a blacklisted Asset and is not accessible.")

    # TODO : maybe we should keep iter design for time dependent collections (OHLC, timeseries, etc.)
    #     And have key addressing only for time independent collections (index is obvious for humans - not a cryptic timestamp)...
    def __iter__(self):
        return iter(self.impl.keys())

    def __len__(self):
        return len(self.impl)


if __name__ == '__main__':

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

    loop.run_until_complete(balance_retrieve_nosession())

    loop.close()


