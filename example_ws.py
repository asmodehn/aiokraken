

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



####
import asyncio
import signal
from aiokraken import WssClient


def process_message(message):
    print(f'processed message {message}')


async def basicbot(loop):
    # NO API KEY here, we deal only with public interface
    ws_kraken = WssClient()

    try:

        wss_kraken = WssClient()

        asyncio.ensure_future(
            wss_kraken.create_connection(process_message)
        )
        await wss_kraken.subscribe(
            ['XBT/USD'],
            {
                "name": 'ticker'
            }
        )
        await wss_kraken.subscribe(
            ['ETH/USD'],
            {
                "name": '*'
            }
        )

        # seems we can reuse the client here... (still same account on same exchange)
        while True:
            await asyncio.sleep(1)

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
