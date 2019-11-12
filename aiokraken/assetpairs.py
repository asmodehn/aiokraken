import asyncio
import time
from collections.abc import Mapping


import typing

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel
from aiokraken.rest.schemas.korderdescr import KOrderDescrOnePrice, KOrderDescr

LOGGER = get_kraken_logger(__name__)


# TODO : unicity of the class in the semantics here (we connect to one exchange only)
#  => use module and setup on import, instead of class ?? Think about (Functional) Domain Model Representation...
#  Remember : python is better as a set of fancy scripts.
class AssetPairs(Mapping):

    def __init__(self, rest_client=None):  # refresh period as none means never.
        self.rest_kraken = rest_client or RestClient()
        self.pairs = None

    async def __call__(self, assets):
        """

        :param assets:
        :param loop_period: a falsy loop_period will prevent looping
        :return:
        """
        self.pairs = (await self.rest_kraken.assetpairs(assets=assets))
        return self

    def __getitem__(self, key):
        if self.pairs is None:
            raise KeyError
        return self.pairs[key]

    def __iter__(self):
        if self.pairs is None:
            raise StopIteration
        return iter(self.pairs)

    def __len__(self):
        if self.pairs is None:
            return 0
        return len(self.pairs)


if __name__ == '__main__':

    async def assetpairs_retrieve_nosession():
        pairs = AssetPairs()
        await pairs(["XBTEUR"])
        for k, p in pairs.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assetpairs_retrieve_nosession())

    loop.close()


