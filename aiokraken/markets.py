import asyncio
import time
from collections.abc import Mapping


import typing
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from aiokraken.marketdata import MarketData
from aiokraken.model.assetpair import AssetPair

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel
from aiokraken.rest.schemas.korderdescr import KOrderDescrOnePrice, KOrderDescr
from aiokraken.utils.filter import Filter

LOGGER = get_kraken_logger(__name__)


# TODO : unicity of the class in the semantics here (we connect to one exchange only)
#  => use module and setup on import, instead of class ?? Think about (Functional) Domain Model Representation...
#  Remember : python is better as a set of fancy scripts.
# TODO : favor immutability (see pyrsistent)
class Markets(Mapping):

    _filter: Filter
    details: typing.Dict[str, AssetPair]  # These are interesting for the developer,
    # but most should be implicit for user of aiokraken -> no need to make it easy to use.
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    impl: typing.Dict[str, MarketData]  # These are supposed to be used regularly

    def __init__(self, restclient: RestClient = None, valid_time: timedelta = None):
        self._filter = Filter(blacklist=[])
        self.restclient = RestClient() if restclient is None else restclient  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid

        self.impl = dict()

    def filter(self,  whitelist=None, blacklist=None, default_allow = True):
        """
        interactive filtering of the instance
        :return:
        """
        f = Filter(whitelist=whitelist, blacklist=blacklist, default_allow=default_allow)
        self._filter = self._filter + f

    async def __call__(self):
        """
        Trigger the actual retrieval of the market details, through the rest client.
        :param rest_client: optional
        # TODO: refresh this periodically ?
        :return:
        """
        if self._filter.whitelist:
            self.details = await self.restclient.assetpairs(assets=self._filter.whitelist)()
        else:
            self.details = await self.restclient.assetpairs()()

        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        def initdata(key):
            self.impl.setdefault(key, MarketData(pair=self.details[key], restclient=self.restclient))  # instantiate if needed
            return self.impl[key]

        if (key in self._filter.whitelist) or self._filter.default:
            if key in self.details:
                return initdata(key)
            else:
                # we need to be able to query by altname as well
                revdict = {p.altname: n for n, p in self.details.items()}
                if key in revdict:
                    return initdata(revdict[key])
                else:
                    raise KeyError(f"{key} is not a pair name nor an altname")
        else:
            raise KeyError(f"{key} is a blacklisted Asset and is not accessible.")

    def __iter__(self):
        return iter(self.details.keys())

    def __len__(self):
        return len(self.details)
    #
    # def __getitem__(self, key):
    #     if self.markets is None:
    #         raise KeyError
    #     return self.markets[key]
    #
    # def __iter__(self):
    #     if self.markets is None:
    #         raise StopIteration
    #     return iter(self.markets)
    #
    # def __len__(self):
    #     if self.markets is None:
    #         return 0
    #     return len(self.markets)


if __name__ == '__main__':

    mkts = Markets()

    async def assetpairs_retrieve_nosession():
        await mkts()
        for k, p in mkts.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assetpairs_retrieve_nosession())
    time.sleep(1)

    loop.run_until_complete(assetpairs_retrieve_nosession())

    loop.close()


