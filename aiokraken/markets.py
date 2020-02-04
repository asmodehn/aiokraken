import asyncio
import time
from collections.abc import Mapping


import typing
from datetime import datetime, timedelta
from decimal import Decimal

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
    impl: typing.Dict[str, AssetPair]
    updated: datetime    # TODO : maybe use traitlets (see ipython) for a more implicit/interactive management of time here ??
    validtime: timedelta

    def __init__(self, restclient: RestClient = None, valid_time: timedelta = None):
        self._filter = Filter(blacklist=[])
        self.restclient = restclient  # default restclient is possible here, but only usable for public requests...
        self.validtime = valid_time   # None means always valid
        # TODO : implement filter by filtering balance view

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
            self.impl = await self.restclient.assetpairs(assets=self._filter.whitelist)()
        else:
            self.impl = await self.restclient.assetpairs()()

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


