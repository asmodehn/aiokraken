""" AIOKraken rest client """
import asyncio
import datetime
import functools
import ssl
import time

import aiohttp
import typing

from aiokraken.rest.schemas.kclosedorder import KClosedOrderModel
from async_property import async_property, async_cached_property

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
from timecontrol import calllimiter

# maybe later to help with better logging...
from timecontrol import eventful

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

    # TODO : better async design... maybe session building as part of theclass, or maybe no class ???
    def __init__(self, server = None, loop=None, protocol = "https://"):
        self.server = server or Server()
        if loop is None:
            try:
                loop = asyncio.get_event_loop()  # TODO : fix this : will break on the second call ?!?!
            except RuntimeError as re:
                # TODO : or a better policy ?? but maybe it depends on python version ??
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        self.loop = loop

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

    # TODO : verify if actually useful ??
    @async_cached_property
    async def assets(self) -> typing.Union[Assets, typing.Coroutine[None, None, Assets]]:
        """ Async property, caching the retrieved Assets """
        # this will store retrieved data into self._assets
        # but we want a cached property to be able to call this synchronously
        return await self.retrieve_assets()

    # TODO : verify if actually useful ??
    @async_cached_property
    async def assetpairs(self) -> typing.Union[AssetPairs, typing.Coroutine[None, None, AssetPairs]]:
        """ Async property, caching the retrieved AssetPairs """
        # this will store retrieved data into self._assetpairs
        # but we want a cached property to be able to call this synchronously
        return await self.retrieve_assetpairs()

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
        if self._assets is None:  # we only need it once !
            req = self.server.assets(assets=assets)   # returns the request to be made for this API.)
            # This request is special, because it will give us more information about other possible requests.
            resp = await self._get(request=req)
            self._assets = Assets(assets_as_dict=resp)
        return self._assets

    @public_limiter
    async def retrieve_assetpairs(self, pairs: typing.Optional[typing.List[typing.Union[AssetPair, str]]]=None) -> AssetPairs:
        """ make assetpairs request to kraken api"""
        if self._assetpairs is None:  # we only need it once !
            req = self.server.assetpair(pairs=pairs)   # returns the request to be made for this API.)
            # This request is special, because it will give us more information about other possible requests.
            resp = await self._get(request=req)
            self._assetpairs = AssetPairs(assetpairs_as_dict=resp)
        return self._assetpairs

    @public_limiter  # skippable because OHLC is not supposed to change very often, and changes should apper in later results.
    async def ohlc(self, pair: typing.Union[AssetPair, str], interval: KTimeFrameModel = KTimeFrameModel.one_minute) -> OHLC:  # TODO: make pair mandatory
        """ make ohlc request to kraken api"""

        # cleaning up pair list
        if isinstance(pair, AssetPair):
            pair_proper = pair
        else:
            cleanpairs = await self.retrieve_assetpairs()
            pair_proper = cleanpairs[pair]
        pair = pair_proper

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
    async def ticker(self, pairs: typing.Optional[typing.List[typing.Union[str, AssetPair]]]=None):  # TODO : model currency pair/'market' in ccxt (see crypy)
        """ make public requests to kraken api"""

        # cleaning up pair list
        pair_proper = [p for p in pairs if isinstance(p, AssetPair)]
        if len(pairs) > len(pair_proper):
            # retrieving assetpairs if necessary
            cleanpairs = await self.retrieve_assetpairs(pairs=pairs)
            pair_translated = [cleanpairs[p] for p in pairs if not isinstance(p, Asset)]
            pairs = pair_proper + pair_translated
        else:
            pairs = pair_proper

        req = self.server.ticker(pairs=pairs)   # returns the request to be made for this API.)
        return await self._get(request=req)

    @private_limiter
    async def openorders(self, trades=False):  # TODO : trades
        """ make private openorders request to kraken api"""

        req = self.server.openorders(trades=trades)   # returns the request to be made for this API.)
        return await self._post(request=req)

    @private_limiter
    async def closedorders(self, trades=False, start: datetime =None, end: datetime = None, offset = 0) -> typing.Tuple[typing.Dict[str, KClosedOrderModel], int]:  # offset 0 or None ??
        """ make private closedorders request to kraken api"""
        # Note : here there is no filtering by assetpair from Kraken API, it needs to be managed one level up...
        if end is None:
            end = datetime.datetime.now()
        if start is None:
            start = datetime.datetime(year=1970, month=1, day=1, hour=1)  # EPOCH

        req = self.server.closedorders(trades=trades, start=int(start.timestamp()), end=int(end.timestamp()), offset=offset)
        corders_list, count = await self._post(request=req)
        return corders_list, count  # making multiple return explicit in interface

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
        if end is None:
            end = datetime.datetime.now()
        if start is None:
            start = datetime.datetime(year=1970, month=1, day=1, hour=1)  # EPOCH

        req = self.server.trades_history(start=int(start.timestamp()), end=int(end.timestamp()), offset = offset)
        trades_list, count = await self._post(request=req)
        return trades_list, count  # making multiple return explicit in interface

    @private_limiter
    async def ledgers(self, start: datetime =None, end: datetime = None, asset: typing.Optional[typing.List[typing.Union[Asset, str]]] = None, offset=0) -> typing.Tuple[typing.Dict[str, KLedgerInfo], int]:
        """ make ledgers requests to kraken api """

        # cleaning up asset list
        if asset is not None:  # means for all assets
            asset_proper = [a for a in asset if isinstance(a, Asset)]
            if len(asset) > len(asset_proper):
                # retrieving assets if necessary
                cleanassets = await self.retrieve_assets()
                asset_translated = [cleanassets[a] for a in asset if not isinstance(a, Asset)]
                asset = asset_proper + asset_translated
            else:
                asset = asset_proper

        if end is None:
            end = datetime.datetime.now()
        end = int(end.timestamp())

        if start is None:
            start = 0  # EPOCH , ie. a long long time ago
        else:
            start = int(start.timestamp())

        req = self.server.ledgers(asset=asset, start=start, end=end, offset=offset)
        more_ledgers, count = await self._post(request=req)
        return more_ledgers, count  # making multiple return explicit in interface

    @private_limiter
    async def websockets_token(self):
        req = self.server.websocket_token()
        token = await self._post(request=req)
        return token


if __name__ == '__main__':

    client = RestClient()

    print(asyncio.run(client.retrieve_assets()))

    print(asyncio.run(client.retrieve_assetpairs()))

    # TMP : TODO : manage local copy of kraken clock...
    # print(client.time())

    # Just testing private endpoint authentication

    from aiokraken.config import load_api_keyfile
    from aiokraken.rest.api import Server

    keystruct = load_api_keyfile()
    priv_client = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))
    print(asyncio.run(priv_client.balance()))
    print(asyncio.run(priv_client.websockets_token()))
