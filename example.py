

# TODO : loop watching ohlc and printing...
#  Note : time synchronization should also be done in the background...
#  We need extensive testing for stability...

import time
from decimal import Decimal, localcontext, DefaultContext

import aiohttp
import asyncio
import signal

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

LOGGER = get_kraken_logger(__name__)

import aiokraken

# We need to initiate singletons here.
# import should not have any side effect.

# Clients

from aiokraken.config import load_api_keyfile

keystruct = load_api_keyfile()
rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                       secret=keystruct.get('secret')))

# WebSocket
# TODO ws_kraken = WssClient()

# get a model for all assets
assets = aiokraken.Assets(rest_kraken=rest_kraken)

# get a model for all asset pairs
assetpairs = aiokraken.AssetPairs(rest_client=rest_kraken)


@asyncio.coroutine
def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    yield from asyncio.sleep(1.0)
    asyncio.get_event_loop().stop()


async def basicbot(loop):
    # NO API KEY here, we deal only with public interface
    rest_kraken = RestClient(server=Server())

    # Pick one asset pair to use as example
    # Get ohlc for it

    # get a model for OHLC, possibly stitched over a long period...
    # TODO ohlc = aiokraken.OHLC(assetpairs["XBTEUR"])

    try:
        # We now can run async code naturally.
        # On first call, it shouldn't be slowed down.
        # Then periodic call will trampoline itself.
        await assets(assets=[])
        await assetpairs(assets=[])

        while True:

            # ohlc = (await rest_kraken.ohlc(pair=["XBTEUR"]))

            print(f"Sleeping a bit longer... {len(assets)} Assets, {len(assetpairs)} Pairs")
            await asyncio.sleep(delay=2)

    except Exception as e:
        LOGGER.error(f"Exception caught : {e}. Terminating...", exc_info=True)
        raise
    finally:
        # TODO : cleanup (cancel all tasks, maybe cancel orders, etc.)
        await rest_kraken.close()


loop = asyncio.get_event_loop()

for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(
        getattr(signal, signame),
        lambda: asyncio.ensure_future(ask_exit(signame))
    )

loop.run_until_complete(basicbot(loop))
