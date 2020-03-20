

# TODO : rewriting client...


import asyncio
import json
import aiohttp
from asyncio import InvalidStateError, CancelledError

import typing
import wrapt

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
SANDBOX_URL = 'wss://ws-sandbox.kraken.com'
PRODUCTION_URL = 'wss://ws.kraken.com'


class WssClient:
    """ asyncio websocket client for kraken.
        The client manages the connections.
        The subscription and data parsing should be managed via the API.
    """

    def __init__(self, api: WSAPI, loop=None):  #API here is supposed to give us the interface (just like for rest), while client is the "thing" the user interracts with...

        #  We need to pass hte loop to hook it up to any potentially preexisting loop
        self.loop = loop if loop is not None else asyncio.get_event_loop()

        self.reqid = 1

        self.connections = {}
        self.connections_status = dict()

        headers = {
            'User-Agent': 'aiokraken'
        }
        self.api = api
        # TODO : DeprecationWarning: The object should be created from async function
        self.session = aiohttp.ClientSession(headers=headers, raise_for_status=True)

        # REMINDER : channels and callbackas are managed in the API directly.
        # Client takes care of connections and requests (not callbacks)
        # TODO : how about responses ? we should find similar design with the REST client for consistency

        self._expected_event = set()

        self._runtask = self.loop.create_task(
            self(callback=self.api)
        )

    async def __call__(self, callback, connection_name="main", connection_env='production'):
        """ Create a new websocket connection and extracts messages from it """
        websocket_url = PRODUCTION_URL if connection_env == 'production' else SANDBOX_URL

        try:
            async with self.session.ws_connect(websocket_url) as ws:
                self.connections[connection_name] = ws
                async for msg in ws:  # REF:https://docs.kraken.com/websockets/#info
                    if msg.type == aiohttp.WSMsgType.TEXT:

                        # to avoid flying blind we first need to parse json into python
                        data = json.loads(msg.data)
                        if isinstance(data, list):
                            self.api(data)

                        elif isinstance(data, dict):
                            # special cases
                            # TODO : LOG everything, somewhere...  and document how to display it...
                            if data.get('event') == 'systemStatus':
                                sysst = SystemStatusSchema().load(data)
                                self.api.systemStatus(sysst)
                                self.connections_status[connection_name] = sysst
                            elif data.get('event') == 'heartbeat':
                                pass  # TODO : something that will shout when heartbeat doesnt arrive on time...
                            elif data.get('event') == 'subscriptionStatus':
                                subst = SubscriptionStatusSchema().load(data)
                                # this will create a channel in WSAPI
                                self.api.subscriptionStatus(subst)
                            else:

                                print(data)
                                raise RuntimeWarning(f"Unexpected event ! : {data}")

                        else:

                            print(data)
                            raise RuntimeWarning(f"Unexpected message data ! : {data}")

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
            print(" !!! RUnning client interrupted, restarting...")
            self._runtask = self.loop.create_task(
                self(callback=self.api, connection_name=connection_name, connection_env=connection_env)
            )
            # TODO: save subscriptions and resubscribe automatically...

    def __del__(self):
        if self._runtask:  # we can stop the running task if this instance disappears
            self._runtask.cancel()

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

    def ping(self):
        pass  # TODO : a method for "acting" on the environment

    def pong(self):
        pass  # TODO : a decorator that point to the "acted on"/callback
              #  when change in environemnt is detected (msg received)

    async def ticker(self, pairs: typing.List[AssetPair], callback: typing.Callable):
        """ subscribe to the ticker update stream.
        if the returned wrapper is not used, the message will still be parsed,
        until the appropriate wrapper (stored in _callbacks) is called.
        """

        # TODO : expect subscription status
        subs_data = self.api.ticker(pairs=pairs, callback=callback)

        await self.subscribe(subs_data, connection_name="main")


if __name__ == '__main__':

    rest_kraken = RestClient()
    wss_kraken = WssClient(api=WSAPI())

    # this will retrieve assetpairs and pick the one we want
    xbt_eur = rest_kraken.sync_assetpairs().get("XXBTZEUR")

    def ticker_update(message):
        print(f'ticker update: {message}')

    async def ticker_sub(pairs):
        await wss_kraken.ticker(pairs=pairs, callback=ticker_update)

    @asyncio.coroutine
    def ask_exit(sig_name):
        print("got signal %s: exit" % sig_name)
        yield from asyncio.sleep(2.0)
        asyncio.get_event_loop().stop()

    import signal
    for signame in ('SIGINT', 'SIGTERM'):
        wss_kraken.loop.add_signal_handler(
            getattr(signal, signame),
            lambda: asyncio.ensure_future(ask_exit(signame))
        )
    wss_kraken.loop.run_until_complete(ticker_sub([xbt_eur]))
    wss_kraken.loop.run_forever()
