import asyncio
import dataclasses
import time
from collections import OrderedDict
from collections.abc import Mapping

from pprint import pprint

import typing

from aiokraken.tinymodel import TinyModel, TinyMutableModel, mutate
from tinydb import TinyDB

from aiokraken.config import load_persist
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

    def __init__(self, blacklist = None, whitelist=None):
        self._blacklist = blacklist   # NONE black list means everything forbidden. Empty list means EVERYTHING ALLOWED.
        self._whitelist = whitelist   # NONE white list means everything allowed. Empty list means NOTHNG ALLOWED.

        # Model is mutable here because htere is no ambiguity to who is hte master/writer of data (remote)
        self._model = TinyModel("Assets", persist_db = load_persist())

    async def __call__(self, rest_client=None):
        """
        :return:
        """
        rest_client = rest_client or RestClient()
        # On retrieval white list determines what data is knowable into the system.
        assets_run = rest_client.assets(assets=self._whitelist) if self._whitelist else rest_client.assets()  # get all
        assets = await assets_run()

        with mutate(self._model) as mm:
            for k, v in assets.items():  # Only when master is remote
                mm[k] = dataclasses.asdict(v)

        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if key not in self._blacklist:  # filtering on local access based on blacklist.
            return self._model[key]
        else:
            raise KeyError(f"{key} is marked as undesired Asset and is not accessible.")

    def __iter__(self):
        return iter(self._model.keys())

    def __len__(self):
        return len(self._model)


if __name__ == '__main__':

    async def assets_retrieve_nosession():
        assets = Assets(blacklist=[])
        await assets()
        for k, p in assets.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()




