

# TODO : rewriting client...


import asyncio
import json
import aiohttp
from asyncio import InvalidStateError, CancelledError

import typing
import wrapt
from aiokraken.model.asset import Asset

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe, UnsubscribeSchema

from aiokraken.websockets.schemas.pingpong import PingSchema

from aiokraken import RestClient
from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscribe import SubscribeSchema, Subscribe

from aiokraken.websockets.api import WSAPI

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema

from aiokraken.websockets.schemas.subscriptionstatus import SubscriptionStatusSchema, SubscriptionStatus

from aiokraken.utils import get_kraken_logger
from aiokraken.websockets.schemas.systemstatus import SystemStatusSchema

LOGGER = get_kraken_logger(__name__)
BETA_URL = 'wss://beta-ws.kraken.com '
PRODUCTION_URL = 'wss://ws.kraken.com'
BETA_URL_AUTH = 'wss://beta-ws-auth.kraken.com '
PRODUCTION_URL_AUTH = 'wss://ws-auth.kraken.com'

# TODO :public/private distinction here is similar to the REST public/private distinction.
#  We should probably deal with it in a similar way (which one ???)

# TODO : beta/ production is also similar. how to deal with it cleanly ?


class WssClient:
    """ asyncio websocket client for kraken.
        The client manages the connections.
        The subscription and data parsing should be managed via the API.
    """

    def __init__(self, api: WSAPI =None, loop=None, restclient=None):
        # API here is supposed to help us define the interface (just like for rest),
        # while client is the "thing" the user interracts with...

        #  We need to pass the loop to hook it up to any potentially preexisting loop
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        # TODO : follow aiohttp design :enforce the loop to exist.
        #  => Use get_running_loop() with a nice error message ??

        # TODO : probably need to support multiple callbacks:
        #  add the client ones to the one passed via optional WSAPI instance
        self.api = api if api is not None else WSAPI(heartbeat_cb=self._heartbeat, systemStatus_cb=self._systemStatus)

        self.restclient = restclient if restclient is not None else RestClient()
        # we need a rest client to get proper assets and pairs
        # TODO : there should only ever be ONE restclient... for the whole python process => simplifiable

        self.connections = {}
        self.connections_status = dict()

        headers = {
            'User-Agent': 'aiokraken'
        }

        self.session = aiohttp.ClientSession(headers=headers, raise_for_status=True)

        # REMINDER : channels and callbacks are managed in the API directly.
        # Client takes care of connections and requests (not callbacks)
        # TODO : how about responses ? we should find similar design with the REST client for consistency

        self._expected_event = set()

        # Note HOW the instance is scheduling itself to run (in async)
        #  as well as providing async entrypoints for library user.
        self._runtask = self.loop.create_task(
            self(callback=self.api)
        )
        # TODO : We should try to converge both rest and wss clients designs.

    async def __call__(self, callback, connection_name="main", connection_env='production'):
        """ Create a new websocket connection and extracts messages from it """
        websocket_url = PRODUCTION_URL if connection_env == 'production' else BETA_URL

        try:
            async with self.session.ws_connect(websocket_url) as ws:
                self.connections[connection_name] = ws
                async for msg in ws:  # REF:https://docs.kraken.com/websockets/#info
                    if msg.type == aiohttp.WSMsgType.TEXT:

                        # to avoid flying blind we first need to parse json into python
                        data = json.loads(msg.data)

                        callback(data)

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        LOGGER.error(f'{msg}')
                        LOGGER.error(f'{msg.type}')
                        LOGGER.error(f'{msg.data}')
                        break
                    else:
                        LOGGER.error(f'{msg}')
                        LOGGER.error(f'{msg.type}')
                        LOGGER.error(f'{msg.data}')
                        break
        # in case internet connection fails try and reconnect automatically after 5 seconds
        # there will be no subscriptions though...
        except aiohttp.ClientConnectionError:
            await asyncio.sleep(5)
            print(" !!! Running client interrupted, restarting...")
            self._runtask = self.loop.create_task(
                self(callback=self.api, connection_name=connection_name, connection_env=connection_env)
            )
            # TODO: save subscriptions and resubscribe automatically...

        except Exception as e:
            # Here because we nedd to manage our exceptions here, and not blindly rely on the async framework...
            print(e)
            raise

    def __del__(self):
        if self._runtask:  # we can stop the running task if this instance disappears
            self._runtask.cancel()

    def _heartbeat(self, msg):
        # TODO : something that will shout when heartbeat doesnt arrive on time...
        # This is supposed to help manage connections
        pass

    def _systemStatus(self, msg):
        # TODO : something that will shout when heartbeat doesnt arrive on time...
        # This is supposed to help manage connections
        pass


    async def ping(self):
        print("PING")
        # TODO : expect pong
        ping_data = self.api.ping(callback=self.pong)

        # TODO : better management of connections here...
        ws = self.connections["main"]

        schema = PingSchema()
        strdata = schema.dumps(ping_data)

        await ws.send_str(strdata, connection_name="main")

    def pong(self):
        print("PONG")
        # TODO : something that shout when pong takes too long to arrive after a ping
        # This is supposed to help manage connections
        pass

    async def close_connection(self, connection_name='main'):
        """ close  websocket connection """
        LOGGER.info('closing the websocket connection')
        resp = await self.connections[connection_name].close()
        del self.connections[connection_name]
        LOGGER.info(f'close response {resp}')

    async def subscribe(self, subdata: Subscribe, connection_name="main"):
        """ add new subscription """
        while connection_name not in self.connections:
            await asyncio.sleep(0.1)
        ws = self.connections[connection_name]
        schema = SubscribeSchema()
        strdata = schema.dumps(subdata)

        # TODO : generate a schema based on what we expect ?
        # self._expected_event["subscriptionStatus"] += SubscriptionStatus()

        await ws.send_str(strdata)

    async def unsubscribe(self, unsubdata: Unsubscribe, connection_name='main'):
        """ stops a subscription """
        while connection_name not in self.connections:
            await asyncio.sleep(0.1)

        ws = self.connections[connection_name]
        schema = UnsubscribeSchema()
        strdata = schema.dumps(unsubdata)

        # TODO : generate a schema based on what we expect ?
        # self._expected_event["subscriptionStatus"] += SubscriptionStatus()

        await ws.send_str(strdata)

    # TODO : maybe we need contextmanagers here to cleanly unsubscribe after use...

    async def ticker(self, pairs: typing.List[typing.Union[str, AssetPair]], callback: typing.Callable):
        """ subscribe to the ticker update stream.
        if the returned wrapper is not used, the message will still be parsed,
        until the appropriate wrapper (stored in _callbacks) is called.
        """
        # we need to depend on restclient for usability
        pairs = [(await self.restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

        # TODO : expect subscription status
        subs_data = self.api.ticker(pairs=pairs, callback=callback)

        await self.subscribe(subs_data, connection_name="main")

        #TODO : what to return here ? something that can "hold the subscription" and manage the unsubscribe when needed...

    async def ohlc(self, pairs: typing.List[typing.Union[str, AssetPair]], callback: typing.Callable, interval: int = 1):
        """ subscribe to the ticker update stream.
        if the returned wrapper is not used, the message will still be parsed,
        until the appropriate wrapper (stored in _callbacks) is called.
        """
        # we need to depend on restclient for usability
        pairs = [(await self.restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

        # TODO : store subscription status to avoid duplication and keep track for cleanup later...

        subs_data = self.api.ohlc(pairs=pairs, interval=interval, callback=callback)

        # if self._subs.get((pairs, interval)) is None:

        # TODO : expect subscription status
        await self.subscribe(subs_data, connection_name="main")
        # else: we already subscribe to it, we just need to add a callback.

        #TODO : what to return here ? something that can "hold the subscription" and manage the unsubscribe when needed...

    async def trades(self, pairs: typing.List[typing.Union[str, AssetPair]], callback: typing.Callable,):
        # we need to depend on restclient for usability
        pairs = [(await self.restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

        # TODO : store subscription status to avoid duplication and keep track for cleanup later...

        subs_data = self.api.trades(pairs= pairs, callback=callback)

        # TODO : expect subscription status
        await self.subscribe(subs_data, connection_name="main")
        # else: we already subscribe to it, we just need to add a callback.


if __name__ == '__main__':

    def ticker_update(message):
        print(f'ticker update: {message}')

    def ohlc_update(message):
        print(f'ohlc update: {message}')

    def ohlc_update2(message):
        print(f'ohlc update BIS: {message}')

    def trades_update(message):
        print(f'trades update: {message}')

    async def subsetup(pairs, wss_kraken):
        # # this will validate the pairs via the rest client
        # await wss_kraken.ticker(pairs=pairs, callback=ticker_update)
        # # mutiple subscribe with different callbacks => only one channel with two callbacks
        # await wss_kraken.ohlc(pairs=pairs, callback=ohlc_update)
        # await wss_kraken.ohlc(pairs=pairs, callback=ohlc_update2)
        await wss_kraken.trades(pairs=pairs, callback=trades_update)

    async def ask_exit(sig_name):
        print("got signal %s: exit" % sig_name)
        await asyncio.sleep(1.0)
        asyncio.get_event_loop().stop()

    async def main():
        wss_kraken = WssClient()  # because wssclient should be created inside a loop
        # Here we are following aiohttp.ClientSession design, forcing the user to manage the event loop.

        import signal
        for signame in ('SIGINT', 'SIGTERM'):
            wss_kraken.loop.add_signal_handler(
                getattr(signal, signame),
                lambda: asyncio.ensure_future(ask_exit(signame))
            )
        wss_kraken.loop.create_task(subsetup(["XXBTZEUR"], wss_kraken))

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
