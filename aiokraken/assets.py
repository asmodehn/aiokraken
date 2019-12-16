import asyncio
import dataclasses
from collections.abc import Mapping

from aiokraken.config import load_persist
from aiokraken.utils import get_kraken_logger
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.kasset import AssetSchema

LOGGER = get_kraken_logger(__name__)


# TODO : unicity of the class instance in the semantics here (we connect to one exchange only)
#  => use module and setup on import, instead of class ?? Think about (Functional) Domain Model Representation...
#  Remember : python is better as a set of fancy scripts.
class Assets(Mapping):

    def __init__(self, blacklist = None, whitelist=None):
        self._blacklist = blacklist   # NONE black list means everything forbidden. Empty list means EVERYTHING ALLOWED.
        self._whitelist = whitelist   # NONE white list means everything allowed. Empty list means NOTHNG ALLOWED.
        #TODO : a better way ?

    async def __call__(self, rest_client=None):
        """
        :return:
        """
        rest_client = rest_client or RestClient()
        # On retrieval white list determines what data is knowable into the system.
        assets_run = rest_client.assets(assets=self._whitelist) if self._whitelist else rest_client.assets()  # get all
        self.impl = await assets_run()

        return self

    # TODO : howto make display to string / repr ??

    def __getitem__(self, key):
        if key not in self._blacklist:  # filtering on local access based on blacklist.
            return self.impl[key]
        else:
            raise KeyError(f"{key} is marked as undesired Asset and is not accessible.")

    def __iter__(self):
        return iter(self.impl.keys())

    def __len__(self):
        return len(self.impl)


if __name__ == '__main__':

    async def assets_retrieve_nosession():
        assets = Assets(blacklist=[])
        await assets()  # Optional from the moment we have Local storage
        for k, p in assets.items():
            print(f" - {k}: {p}")

    loop = asyncio.get_event_loop()

    loop.run_until_complete(assets_retrieve_nosession())

    loop.close()




