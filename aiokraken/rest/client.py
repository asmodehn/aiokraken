""" AIOKraken rest client """
import asyncio
import functools
import ssl
import urllib
import hashlib
import hmac
import base64
import timeit
import aiohttp
from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API

from aiokraken.rest.schemas.time import TimeSchema
from aiokraken.rest.limiter import limiter

BASE_URL = 'https://api.kraken.com'
LOGGER = get_kraken_logger(__name__)

# TODO : see sans-io to get a clearer picture about how to design this cleanly...

# MINIMAL CLIENT (only control flow & IO)
# Also Time control...

# Because we need one limiter for multiple decorators
public_limiter = limiter(period=3)
private_limiter = limiter(period=5)


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

    # TODO : maybe in Request somehow, and track the "type" (get/post) of request ??
    async def _get(self, request):  # request is coming from the API
        """
        GET request helper. the goal here is to ensure stability.
        :param request:
        :return:
        """
        LOGGER.info(f"GET {request.urlpath}")  # CAREFUL with {request.data}, it can contain keys ! => TODO : lower level, in request ??
        try:
            # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with self.session.post(self.protocol + self.server.url + request.urlpath, headers=request.headers,
                                         data=request.data) as response:
                return await request(response)
                # Note : response log should be done in caller (which can choose if it is appropriate to show or not.
        except (ssl.SSLError, aiohttp.ClientOSError) as err:  # for example : [Errno 104] Connection reset by peer / SSLError
            LOGGER.error(err, exc_info=True)
            # should be ponctual. just try again
            retry_attempt = asyncio.create_task(self.time())
            await retry_attempt  # waiting to get a result
            return retry_attempt.result()
        except aiohttp.ClientConnectorError as err:
            LOGGER.error(err, exc_info=True)
            return {'error': err}
        except aiohttp.ClientResponseError as err:
            LOGGER.error(err, exc_info=True)
            return {'error': err}

    async def _post(self, request):  # request is coming from the API
        """
        POST request helper. the goal here is to ensure stability.
        :param request:
        :return:
        """
        LOGGER.info(
            f"POST {request.urlpath}")  # CAREFUL with {request.data}, it can contain keys ! => TODO : lower level, in request ??
        try:
            # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with self.session.post(self.protocol + self.server.url + request.urlpath, headers=request.headers,
                                         data=request.data) as response:
                return await request(response)
                # Note : response log should be done in caller (which can choose if it is appropriate to show or not.
        except (ssl.SSLError, aiohttp.ClientOSError) as err:  # for example : [Errno 104] Connection reset by peer / SSLError
            LOGGER.error(err, exc_info=True)
            # should be ponctual. just try again
            retry_attempt = asyncio.create_task(self.time())
            await retry_attempt  # waiting to get a result
            return retry_attempt.result()
        except aiohttp.ClientConnectorError as err:
            LOGGER.error(err, exc_info=True)
            return {'error': err}
        except aiohttp.ClientResponseError as err:
            LOGGER.error(err, exc_info=True)
            return {'error': err}

    @public_limiter(skippable=True)
    async def time(self):
        """ make public requests to kraken api"""

        req = self.server.time()   # returns the request to be made for this API.
        return await self._get(request=req)

    @public_limiter(skippable=True)
    async def assets(self, assets=None):
        """ make public requests to kraken api"""

        req = self.server.assets(assets=assets)   # returns the request to be made for this API.)
        return await self._get(request=req)

    @public_limiter(skippable=True)
    async def assetpairs(self, assets=None):
        """ make public requests to kraken api"""

        req = self.server.assetpair(assets=assets)   # returns the request to be made for this API.)
        return await self._get(request=req)

    @public_limiter(skippable=True)  # skippable because OHLC is not supposed to change very often, and changes should apper in later results.
    async def ohlc(self, pair='XBTEUR'):
        """ make public requests to kraken api"""

        req = self.server.ohlc(pair=pair)   # returns the request to be made for this API.)
        return await self._get(request=req)

    @private_limiter(skippable=False)
    async def balance(self):
        """ make public requests to kraken api"""

        req = self.server.balance()
        return await self._post(request=req)

    @public_limiter(skippable=False)
    async def ticker(self, pairs=['XBTEUR']):  # TODO : model currency pair/'market' in ccxt (see crypy)
        """ make public requests to kraken api"""

        req = self.server.ticker(pairs=pairs)   # returns the request to be made for this API.)
        return await self._get(request=req)

    @private_limiter(skippable=False)
    async def openorders(self, trades=False):  # TODO : trades
        """ make public requests to kraken api"""

        req = self.server.openorders(trades=trades)   # returns the request to be made for this API.)
        return await self._post(request=req)

    @private_limiter(skippable=False)
    async def addorder(self, order):
        """ make public requests to kraken api"""

        req = self.server.addorder(order=order)
        return await self._post(request=req)

    @private_limiter(skippable=False)
    async def cancel(self, txid_userref):
        """ make public requests to kraken api"""
        # TODO : accept order, (but only use its userref or id)
        req = self.server.cancel(txid_userref = txid_userref)
        return await self._post(request=req)

    async def close(self):
        """ Close aiohttp session """
        await self.session.close()
