""" AIOKraken rest client """
import asyncio
import datetime
import functools
import ssl
import aiohttp
import typing

from aiokraken.model.assetpair import AssetPair

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API

from timecontrol.underlimiter import UnderLimiter
from timecontrol.command import Command

BASE_URL = 'https://api.kraken.com'
LOGGER = get_kraken_logger(__name__)

# TODO : see sans-io to get a clearer picture about how to design this cleanly...

# MINIMAL CLIENT (only control flow & IO)
# Also Time control...


"""
Intent : usability of the API...
"""

# Because we need one limiter for multiple decorators
public_limiter = UnderLimiter(period=3)
private_limiter = UnderLimiter(period=5)
rest_command = Command(timer=datetime.datetime.now)


class RestClient:

    def __init__(self, server = None, protocol = "https://"):
        self.server = server or Server()
        self.protocol = protocol

        self._headers = {  # TODO : aiokraken useragent
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
            )
        }
        self.session = None

        # we store locally assets and pairs to help validate subsequent requests
        self._assets = {}
        self._assetpairs = {}

    async def __aenter__(self):
        """ Initializes a session.
        Although very useful for proper usage, this is not mandatory,
        as per https://docs.aiohttp.org/en/stable/client_reference.html#client-session
        """
        self.session = await aiohttp.ClientSession(headers=self._headers, raise_for_status=True, trust_env=True).__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """ Close aiohttp session """
        await self.session.__aexit__(exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb)

    # TODO : maybe in Request somehow, and track the "type" (get/post) of request ??
    async def _get(self, request):  # request is coming from the API
        """
        GET request helper. the goal here is to ensure stability.
        :param request:
        :return:
        """
        if self.session is None:
            getter = functools.partial(aiohttp.request, method='GET')  # TODO : useragent : common / anonymous.
        else:
            getter = self.session.get

        LOGGER.info(f"GET {request.urlpath}")  # CAREFUL with {request.data}, it can contain keys ! => TODO : lower level, in request ??
        try:
            # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with getter(url=self.protocol + self.server.url + request.urlpath, headers=request.headers,
                                         params=request.data) as response:  # NOTE : for GET, data has to be interpreted as params !
                return await request(response)
                # Note : response log should be done in caller (which can choose if it is appropriate to show or not.
        except (ssl.SSLError, aiohttp.ClientOSError) as err:  # for example : [Errno 104] Connection reset by peer / SSLError
            LOGGER.error(err, exc_info=True)
            # should be ponctual. just try again
            retry_attempt = asyncio.create_task(self.time())
            await retry_attempt  # waiting to get a result
            return retry_attempt.result()
            # TODO : check for error 5XX before retry
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
        if self.session is None:
            poster = functools.partial(aiohttp.request, method='POST')  # TODO : useragent : common / anonymous.
        else:
            poster = self.session.post

        LOGGER.info(
            f"POST {request.urlpath}")  # CAREFUL with {request.data}, it can contain keys ! => TODO : lower level, in request ??
        try:
            # TODO : pass protocol & host into the request url in order to have it displayed when erroring !
            async with poster(url=self.protocol + self.server.url + request.urlpath, headers=request.headers,
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

    @rest_command
    @public_limiter
    async def time(self):
        """ make public requests to kraken api"""

        req = self.server.time()   # returns the request to be made for this API.
        return await self._get(request=req)

    @rest_command
    @public_limiter
    async def assets(self, assets=None):
        """ make assets request to kraken api"""

        req = self.server.assets(assets=assets)   # returns the request to be made for this API.)
        # This request is special, because it will give us more informations about other possible requests.

        self._assets = await self._get(request=req)
        return self._assets

    @rest_command
    @public_limiter
    async def assetpairs(self, assets=None):
        """ make assetpairs request to kraken api"""

        req = self.server.assetpair(assets=assets)   # returns the request to be made for this API.)
        self._assetpairs = await self._get(request=req)
        return self._assetpairs

    @rest_command
    @public_limiter  # skippable because OHLC is not supposed to change very often, and changes should apper in later results.
    async def ohlc(self, pair: typing.Union[AssetPair, str], interval: KTimeFrameModel = KTimeFrameModel.one_minute):  # TODO: make pair mandatory
        """ make ohlc request to kraken api"""
        if isinstance(pair, str):  # Just to be user friendly...
            #  We need the list of markets to validate pair string passed in the request
            if not self._assetpairs:
                req = self.assetpairs()
                await req()
            if not pair in self._assetpairs.keys():
                altname_map = {p.altname: p for n, p in self._assetpairs.items()}
                if not pair in altname_map.keys():
                    # TODO : proper exception class
                    RuntimeError(f"{pair} not in {[k for k in self._assetpairs.keys()]} nor {altname_map.keys()}")
                else:
                    pair = altname_map[pair]  # get the proper type.
            else:
                pair = self._assetpairs[pair]
        elif not isinstance(pair, AssetPair):
            RuntimeError(f"{pair} not of the proper type...")
        # TODO : or maybe we should pass the assetpair from model, and let the api deal with it ??
        req = self.server.ohlc(pair=pair, interval=interval)   # returns the request to be made for this API.)
        resp = await self._get(request=req)
        # Note : marshmallow has already checked that the response pair matches what was requested.
        return resp

    @rest_command
    @private_limiter
    async def balance(self):
        """ make balance requests to kraken api"""

        req = self.server.balance()
        return await self._post(request=req)  # Private request must use POST !

    @rest_command
    @private_limiter
    async def trade_balance(self):
        """ make trade balance requests to kraken api"""

        req = self.server.trade_balance()
        return await self._post(request=req)

    @rest_command
    @public_limiter
    async def ticker(self, pairs=['XBTEUR']):  # TODO : model currency pair/'market' in ccxt (see crypy)
        """ make public requests to kraken api"""

        req = self.server.ticker(pairs=pairs)   # returns the request to be made for this API.)
        return await self._get(request=req)

    @rest_command
    @private_limiter
    async def openorders(self, trades=False):  # TODO : trades
        """ make private openorders request to kraken api"""

        req = self.server.openorders(trades=trades)   # returns the request to be made for this API.)
        return await self._post(request=req)

    @rest_command
    @private_limiter
    async def closedorders(self, trades=False):  # TODO : trades
        """ make private closedorders request to kraken api"""

        req = self.server.closedorders(trades=trades)   # returns the request to be made for this API.)
        return await self._post(request=req)

    @rest_command
    @private_limiter
    async def addorder(self, order):
        """ make public requests to kraken api"""

        req = self.server.addorder(order=order)
        return await self._post(request=req)

    @rest_command
    @private_limiter
    async def cancel(self, txid_userref):
        """ make public requests to kraken api"""
        # TODO : accept order, (but only use its userref or id)
        req = self.server.cancel(txid_userref = txid_userref)
        return await self._post(request=req)

