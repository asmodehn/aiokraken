import asyncio

from aiokraken import RestClient, WssClient
from aiokraken.markets import Markets
from aiokraken.assets import Assets
from aiokraken.balance import Balance

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient


LOGGER = get_kraken_logger(__name__)


class Exchange:  # todo : enforce unicity of this ??  Singleton via metaclass ?? store directly in module ?

    def __init__(self, assets=None, markets=None):
        from aiokraken.config import load_api_keyfile
        keystruct = load_api_keyfile()
        # We load hte key in memory in case we need it later (balance, and more...)
        #  we rely on the RestClient to not make a private request when a public will do the same
        #  to avoid unnecessary signing.
        self.rest = RestClient(server=Server(key=keystruct.get('key'),
                                               secret=keystruct.get('secret')))
        self.wss = WssClient()

        self._assets_sub = assets
        self._markets_sub = markets
        # TODO : some meaningful and useful link between markets and assets ?
        # internal reset behavior
        self.assetpairs = Markets(markets=self._markets_sub)
        self.assets = Assets(assets=self._assets_sub)
        self.balance = Balance(assets=self._assets_sub)
        # Other things need resetting : recreate this.

    async def __aenter__(self):
        # Opens client Session (cannot be done in init or in module import)
        await self.rest.__aenter__()
        try:
            # initializes everything async (cannot be done in init or in module import)
            await self.assets(rest_client=self.rest)
            await self.assetpairs(rest_client=self.rest)
            await self.balance(rest_client=self.rest)
            # Note : assets affect balance considered, markets affect markets considered (TODO)
            # M market and A asset might not be related at all ? cf. with leverage I can trade anything ??
            # Or maybe there is a rule, like a market must have at least one asset as part of the pair ?

            # Goal: provide Guarantees : we can spend only assets in only markets.
            return self

        except Exception as e:
            LOGGER.error(e, exc_info=True)
            raise  # Let someone else reset me...

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rest.__aexit__(exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb)


if __name__ == '__main__':

    # Minimum exchange usage
    # TODO : doctest as well

    async def exchange_info():
        async with Exchange(assets=["EUR", "XBT"], markets=["XBTEUR"]) as c:

            print(c.assets)
            print(c.assetpairs)
            print(c.balance)

    loop = asyncio.get_event_loop()

    loop.run_until_complete(exchange_info())

    loop.close()
