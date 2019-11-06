

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


@asyncio.coroutine
def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    yield from asyncio.sleep(1.0)
    asyncio.get_event_loop().stop()


async def basicbot(loop):
    # NO API KEY here, we deal only with public interface
    rest_kraken = RestClient(server=Server())
    try:

        # seems we can reuse the client here... (still same account on same exchange)
        while True:
            # : For now we pick a pair manually...
            # TODO : Change these to use model object and not direct REST client.
            assets = (await rest_kraken.assets(assets=["XBT", "EUR"]))

            assetpairs = (await rest_kraken.assetpairs(assets=["XBTEUR"]))

            ohlc = (await rest_kraken.ohlc(pair=["XBTEUR"]))

            # TMP : testing limiter with this. should never get us EAPI:Rate limit exceeded

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
