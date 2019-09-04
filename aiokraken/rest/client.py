""" AIOKraken rest client """
import urllib
import hashlib
import hmac
import base64
import timeit
import aiohttp
from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API

BASE_URL = 'https://api.kraken.com'
LOGGER = get_kraken_logger(__name__)


# MINIMAL CLIENT (only control flow & IO)
class RestClient:

    def __init__(self, server, protocol = "https://"):
        self.server = server
        self.protocol = protocol

        _headers = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
            )
        }

        self.session = aiohttp.ClientSession(headers=_headers, raise_for_status=True, trust_env=True)

    async def time(self):
        """ make public requests to kraken api"""

        kt = self.server.time()   # returns the request to be made for this API.
        print(kt.url)
        try:  # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with self.session.post(self.protocol + kt.url, headers=kt.headers, data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def balance(self):
        """ make public requests to kraken api"""

        kt = self.server.balance()
        print(kt.url)
        try:
            async with self.session.post(self.protocol + kt.url, headers=kt.headers, data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def close(self):
        """ Close aiohttp session """
        await self.session.close()


import aiohttp
import asyncio
import signal
LOGGER = get_kraken_logger(__name__)


# EXAMPLE CODE

async def get_time():
    """ get kraken time"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.time()
        print(f'response is {response}')
    finally:
        await rest_kraken.close()


async def get_balance():
    """Start kraken websockets api
    """
    from aiokraken.rest import krak_key
    rest_kraken = RestClient(server=Server(key=krak_key.key,
                                          secret=krak_key.secret))
    response = await rest_kraken.balance()
    await rest_kraken.close()
    print(f'response is {response}')


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

loop.run_until_complete(get_time())
loop.run_until_complete(get_balance())
