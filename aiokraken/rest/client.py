""" AIOKraken rest client """
import asyncio
import datetime
import functools
import ssl
import time

import aiohttp
import typing

from aiokraken.rest.assetpairs import AssetPairs

from aiokraken.rest.assets import Assets

from aiokraken.model.ohlc import OHLC

from aiokraken.rest.schemas.ktrade import KTradeModel

from aiokraken.rest.schemas.kledger import KLedgerInfo

from aiokraken.model.assetpair import AssetPair
from aiokraken.model.asset import Asset
from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.utils import get_kraken_logger, get_nonce
from aiokraken.rest.api import Server, API
from timecontrol.calllimiter import calllimiter

from timecontrol.eventful import eventful

BASE_URL = 'https://api.kraken.com'
LOGGER = get_kraken_logger(__name__)

# TODO : see sans-io to get a clearer picture about how to design this cleanly...

# MINIMAL CLIENT (only control flow & IO)
# Also Time control...


"""
Intent : usability of the API...
"""

# Because we need one limiter for multiple decorators
# public_limiter = UnderLimiter(period=3)
# private_limiter = UnderLimiter(period=5)
# rest_command = Command(timer=datetime.datetime.now)

private_limiter = calllimiter(ratelimit=datetime.timedelta(seconds=5))
public_limiter = calllimiter(ratelimit=datetime.timedelta(seconds=3))


class RestClient:

    def __init__(self, server = None, loop=None, protocol = "https://"):
        self.server = server or Server()
        self.loop = loop if loop is not None else asyncio.get_event_loop()

        self.protocol = protocol

        self._headers = {  # TODO : aiokraken useragent
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
            )
        }
        self.session = None

        # we store locally assets and pairs to help validate subsequent requests
        self._assets = None
        self._assetpairs = None

    @property
    def assets(self) -> typing.Union[Assets, typing.Coroutine[ None, None, Assets]]:
        """ Specific method that can be called both as sync from a sync function, and as async from an async function"""
        if self._assets is None:
            # No point to run this multiple times in one process run.
            if self.loop.is_running():  # if we are already in an eventloop, we just return the coroutine
                return self.retrieve_assets()
            else:  # we run it ourselves before returning
                self.loop.run_until_complete(self.retrieve_assets())
        return self._assets

    @property
    def assetpairs(self) -> typing.Union[Assets, typing.Coroutine[ None, None, Assets]]:
        """ Specific method that can be called both as sync from a sync function, and as async from an async function"""
        if self._assetpairs is None:
            # No point to run this multiple times in one process run.
            if self.loop.is_running():  # if we are already in an eventloop, we just return the coroutine
                return self.retrieve_assetpairs()
            else:  # we run it ourselves before returning
                self.loop.run_until_complete(self.retrieve_assetpairs())
        return self._assetpairs

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

    @public_limiter
    async def time(self):
        """ make public requests to kraken api"""
        # TODO : build a property, similar to assets and assetpairs, but with a local clock, sync with the server clock.
        req = self.server.time()   # returns the request to be made for this API.
        return await self._get(request=req)

    @public_limiter
    async def retrieve_assets(self, assets: typing.Optional[typing.List[typing.Union[Asset, str]]]=None):
        """ make assets request to kraken api"""

        req = self.server.assets(assets=assets)   # returns the request to be made for this API.)
        # This request is special, because it will give us more informations about other possible requests.
        resp = await self._get(request=req)
        self._assets = Assets(assets_as_dict=resp)
        return self._assets

    @public_limiter
    async def retrieve_assetpairs(self, pairs: typing.Optional[typing.List[typing.Union[AssetPair, str]]]=None):
        """ make assetpairs request to kraken api"""

        req = self.server.assetpair(pairs=pairs)   # returns the request to be made for this API.)
        # This request is special, because it will give us more informations about other possible requests.
        resp = await self._get(request=req)
        self._assetpairs = AssetPairs(assetpairs_as_dict=resp)
        return self._assetpairs

    @public_limiter  # skippable because OHLC is not supposed to change very often, and changes should apper in later results.
    async def ohlc(self, pair: typing.Union[AssetPair, str], interval: KTimeFrameModel = KTimeFrameModel.one_minute) -> OHLC:  # TODO: make pair mandatory
        """ make ohlc request to kraken api"""
        pair = self.assetpairs[pair]
        # TODO : or maybe we should pass the assetpair from model, and let the api deal with it ??
        req = self.server.ohlc(pair=pair, interval=interval)   # returns the request to be made for this API.)
        resp = await self._get(request=req)
        # Note : marshmallow has already checked that the response pair matches what was requested.
        return resp

    @private_limiter
    async def balance(self):
        """ make balance requests to kraken api"""
        #  We need the list of assets to return proper types in balance
        if not self._assets:
            await self.retrieve_assets()
        req = self.server.balance()
        resp = await self._post(request=req)  # Private request must use POST !
        return resp.accounts  # Note : this depends on the schema.

    @private_limiter
    async def trade_balance(self):
        """ make trade balance requests to kraken api"""

        req = self.server.trade_balance()
        return await self._post(request=req)

    @public_limiter
    async def ticker(self, pairs: typing.Optional[typing.List[AssetPair]]=None):  # TODO : model currency pair/'market' in ccxt (see crypy)
        """ make public requests to kraken api"""
        pairs = [self.assetpairs[p] for p in pairs] if pairs else []
        req = self.server.ticker(pairs=pairs)   # returns the request to be made for this API.)
        return await self._get(request=req)

    @private_limiter
    async def openorders(self, trades=False):  # TODO : trades
        """ make private openorders request to kraken api"""

        req = self.server.openorders(trades=trades)   # returns the request to be made for this API.)
        return await self._post(request=req)

    @private_limiter
    async def closedorders(self, trades=False):  # TODO : trades
        """ make private closedorders request to kraken api"""

        req = self.server.closedorders(trades=trades)   # returns the request to be made for this API.)
        return await self._post(request=req)

    @private_limiter
    async def addorder(self, order):
        """ make public requests to kraken api"""

        req = self.server.addorder(order=order)
        return await self._post(request=req)

    @private_limiter
    async def cancel(self, txid_userref):
        """ make public requests to kraken api"""
        # TODO : accept order, (but only use its userref or id)
        req = self.server.cancel(txid_userref = txid_userref)
        return await self._post(request=req)

    @private_limiter
    async def trades(self, start: datetime =None, end: datetime = None, offset = 0) -> typing.Tuple[typing.Dict[str, KTradeModel], int]:  # offset 0 or None ??
        """ make tradeshistory requests to kraken api"""
        # Note : here there is no filtering by assetpair from Kraken API, it needs to be managed one level up...
        req = self.server.trades_history(start=int(start.timestamp()), end=int(end.timestamp()), offset = offset)
        trades_list, count = await self._post(request=req)
        return trades_list, count  # making multiple return explicit in interface

    @private_limiter
    async def ledgers(self, asset: typing.Optional[typing.List[typing.Union[Asset, str]]], start: datetime =None, end: datetime = None, offset=0) -> typing.Tuple[typing.Dict[str, KLedgerInfo], int]:
        """ make ledgers requests to kraken api """
        asset = [(await self.assets)[a] for a in asset]  # retrieve the proper asset instance
        req = self.server.ledgers(asset=asset, start=int(start.timestamp()), end=int(end.timestamp()), offset=offset)
        more_ledgers, count = await self._post(request=req)
        return more_ledgers, count  # making multiple return explicit in interface


if __name__ == '__main__':

    client = RestClient()

    print(client.assets)

    print(client.assetpairs)

    # print(client.time())
