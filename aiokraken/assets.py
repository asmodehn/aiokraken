import asyncio
import time
from collections.abc import Mapping

from pprint import pprint

import typing

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

from aiokraken.rest.schemas.krequestorder import RequestOrder
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel
from aiokraken.rest.schemas.korderdescr import KOrderDescrOnePrice, KOrderDescr


LOGGER = get_kraken_logger(__name__)


# TODO : unicity of the class instance in the semantics here (we connect to one exchange only)
#  => use module and setup on import, instead of class ?? Think about (Functional) Domain Model Representation...
#  Remember : python is better as a set of fancy scripts.
class Assets(Mapping):

    def __init__(self, assets = None):  # refresh period as none means never.
        self._desired_assets = assets  # None means all

    async def __call__(self, rest_client=None):
        """
        :return:
        """
        rest_client = rest_client or RestClient()
        assets_run = rest_client.assets(assets=self._desired_assets)
        self.assets = await assets_run()
        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if self.assets is None:
            raise KeyError
        return self.assets[key]

    def __iter__(self):
        if self.assets is None:
            raise StopIteration
        return iter(self.assets)

    def __len__(self):
        if self.assets is None:
            return 0
        return len(self.assets)


if __name__ == '__main__':

    async def assets_retrieve_nosession():
        assets = Assets(["XBT", "EUR"])
        await assets()
        for k, p in assets.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()




