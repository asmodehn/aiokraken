""" AIOKraken rest client """
import urllib
import hashlib
import hmac
import base64
import timeit
import aiohttp
from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API

from aiokraken.rest.schemas.time import TimeSchema

BASE_URL = 'https://api.kraken.com'
LOGGER = get_kraken_logger(__name__)

# TODO : see sans-io to get a clearer picture about how to design this cleanly...

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
        print(kt.urlpath)
        try:  # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers, data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def ohlc(self, pair='XBTEUR'):
        """ make public requests to kraken api"""

        kt = self.server.ohlc(pair=pair)   # returns the request to be made for this API.)
        try:  # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers, data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def balance(self):
        """ make public requests to kraken api"""

        kt = self.server.balance()
        print(kt.urlpath)
        try:
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers, data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def ticker(self, pair='XBTEUR'):
        """ make public requests to kraken api"""

        kt = self.server.ticker(pair=pair)   # returns the request to be made for this API.)
        try:  # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers, data=kt.data) as response:

                return await kt(response)
        except aiohttp.ClientConnectorError as err:
            LOGGER.error(err)
            return {'error': err}
        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def openorders(self, trades=False):
        """ make public requests to kraken api"""

        kt = self.server.openorders(trades=trades)   # returns the request to be made for this API.)
        try:  # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers, data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def bid(self, order):
        """ make public requests to kraken api"""

        kt = self.server.bid(order=order)
        print(kt.urlpath)
        try:
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers,
                                         data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def ask(self, order):
        """ make public requests to kraken api"""

        kt = self.server.ask(order = order)
        print(kt.urlpath)
        try:
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers,
                                         data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def cancel(self, txid_userref):
        """ make public requests to kraken api"""

        kt = self.server.cancel(txid_userref = txid_userref)
        print(kt.urlpath)
        try:
            async with self.session.post(self.protocol + self.server.url + kt.urlpath, headers=kt.headers,
                                         data=kt.data) as response:

                return await kt(response)

        except aiohttp.ClientResponseError as err:
            LOGGER.error(err)
            return {'error': err}

    async def close(self):
        """ Close aiohttp session """
        await self.session.close()
