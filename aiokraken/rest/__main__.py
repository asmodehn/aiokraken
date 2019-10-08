import aiohttp
import asyncio
import signal

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from aiokraken.rest.client import RestClient

LOGGER = get_kraken_logger(__name__)


# Dummy client
# TODO : command line basic client.

async def get_time():
    """ get kraken time"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.time()
        print(f'response is {response}')
    finally:
        await rest_kraken.close()


async def get_ohlc(pair='XBTEUR'):
    """ get kraken time"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.ohlc(pair=pair)
        print(f'response is \n{response.head()}')

        indicators = response.rsi()

        print(f'with IRS indicator \n{indicators.head()}')

    finally:
        await rest_kraken.close()


async def get_balance():
    """Start kraken websockets api
    """
    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    response = await rest_kraken.balance()
    await rest_kraken.close()
    print(f'response is {response}')


async def bid(order):
    """Start kraken websockets api
    """
    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:
        response = await rest_kraken.bid(order=order)
    finally:
        await rest_kraken.close()
    print(f'response is {response}')


async def ask(order):
    """Start kraken websockets api
    """
    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:
        response = await rest_kraken.ask(order=order)
    finally:
        await rest_kraken.close()
    print(f'response is {response}')




# TODO : somehow use ipython shell for this... hooking up to his event loop


@asyncio.coroutine
def ask_exit(sig_name):
    print("got signal %s: exit" % sig_name)
    yield from asyncio.sleep(1.0)
    asyncio.get_event_loop().stop()


loop = asyncio.get_event_loop()

for signame in ('SIGINT', 'SIGTERM'):
    loop.add_signal_handler(
        getattr(signal, signame),
        lambda: asyncio.ensure_future(ask_exit(signame))
    )

# loop.run_until_complete(get_time())
# loop.run_until_complete(get_ohlc())
# loop.run_until_complete(get_balance())

from aiokraken.model.order import MarketOrder

loop.run_until_complete(bid(MarketOrder(pair='XBTEUR', volume='0.01', )))
loop.run_until_complete(ask(MarketOrder(pair='XBTEUR', volume='0.01', )))
