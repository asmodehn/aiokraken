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
# TODO : favor immutability (see pyrsistent)
class Markets(Mapping):

    def __init__(self, markets = None):
        """
        :param markets: the list of markets to filter what we are interested in.
        """
        self._desired_markets = markets  # means all

    async def __call__(self, rest_client=None):
        """
        Trigger the actual retrieval of the market details, through the rest client.
        :param rest_client: optional
        # TODO: refresh this periodically ?
        :return:
        """
        rest_client = rest_client or RestClient()
        # Note : we leave session creation to the context.
        self.markets = (await rest_client.assetpairs(assets=self._desired_markets))
        return self

    def __getitem__(self, key):
        if self.markets is None:
            raise KeyError
        return self.markets[key]

    def __iter__(self):
        if self.markets is None:
            raise StopIteration
        return iter(self.markets)

    def __len__(self):
        if self.markets is None:
            return 0
        return len(self.markets)


if __name__ == '__main__':

    async def assetpairs_retrieve_nosession():
        mkts = Markets(["XBTEUR"])
        await mkts()
        for k, p in mkts.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assetpairs_retrieve_nosession())

    loop.close()


