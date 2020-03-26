import typing
from .client import RestClient, Server

from .assets import Assets
from .assetpairs import AssetPairs


# helpful simple access to data via coroutine, shadowing data module
async def assets(client: typing.Optional[RestClient] = None):
    client = client if client is not None else RestClient()
    return await client.retrieve_assets()


# helpful simple access to data via coroutine, shadowing data module
async def assetpairs(client: typing.Optional[RestClient] = None):
    client = client if client is not None else RestClient()
    return await client.retrieve_assetpairs()


# TODO :  When running rest client, we should log all requests (debugging purposes)
#   But when running whol package with model and a mix of REST and WebSockets, underlying requests should be hidden from displayed log (but stored in file)

__all__ = [
    'RestClient',
    'Server',
    'assets',
    'Assets',
    'assetpairs',
    'AssetPairs',
]

# TODO : this (or model) might be the proper place to introduce the concept of currency
#  (unit based asset value, custom decimal precision. see gitlab.com/asmodehn/barter)

# TODO : this (or model) might be the proper place to introduce the concept of market
#  (assetpair, with properties), since many request want the assetpair as param...
