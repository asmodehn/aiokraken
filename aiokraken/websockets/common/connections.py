import asyncio
import contextlib
import inspect
import json
from dataclasses import dataclass

import aiohttp
import typing

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe, UnsubscribeSchema

from aiokraken.websockets.schemas.subscribe import Subscribe, SubscribeSchema

from aiokraken.utils import get_kraken_logger

LOGGER = get_kraken_logger(__name__)

connections = {}
connections_status = dict()  # TODO : maybe dict is not useful ??


headers = {
    'User-Agent': 'aiokraken'
}

# One and only one per process, ie per module (instantiated in interpreter)
session: typing.Optional[aiohttp.ClientSession] = None

from aiokraken.websockets.common.onsignal import onsignal
# this should have monkey patched asyncio eventloop ...


class WssConnection:  # instance per URL !
    websocket_url: str  # TODO : more precise type
    connection: typing.Optional[aiohttp.ClientWebSocketResponse]

    # the whole point of this class : track subscriptions by connection...
    subscribed: typing.List[Subscribe]

    @staticmethod
    async def session_cleanup(sig=None):
        global session
        if sig:
            print(f"signal {sig} caught !")
        print("Closing aiohttp session...")
        # Note : this will close connections
        if session is not None:
            await session.close()
            session = None

    @staticmethod
    async def session_create():  # async because a running loop is needed !
        global session  # TODO : global session or connection attribute ?
        if session is None:
            # Note : async loop must already be running here.
            session = aiohttp.ClientSession(headers=headers, raise_for_status=True)
            # adding signal handler to close the loop on int/term signal
            session._loop.onsignal('SIGINT', 'SIGTERM')(WssConnection.session_cleanup)

    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.connection = None
        self._handlers = dict()

    def __call__(self, wsmsgtype: aiohttp.WSMsgType):
        def decorator(handler):
            # pattern matching on aiohttp.WSMsgType
            self._handlers.setdefault(wsmsgtype, [])
            self._handlers[wsmsgtype].append(handler)
            return handler
        return decorator

    async def __aiter__(self):
        # TODO : add static counter to count reentrency and fail before too deep recursion...
        await self.session_create()

        # TODO : handle connection/websocket errors here
        #  to provide sticky connection (and linearization of messages for a given protocol)...
        try:
            async with session.ws_connect(self.websocket_url) as conn:
                self.connection = conn
                async for msg in self.connection:  # REF:https://docs.kraken.com/websockets/#info
                    if msg.type == aiohttp.WSMsgType.TEXT and msg.type in self._handlers:
                        for h in self._handlers[aiohttp.WSMsgType.TEXT]:
                            h(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR and msg.type in self._handlers:
                        for h in self._handlers[aiohttp.WSMsgType.ERROR]:
                            h(msg.data)
                    else:  # unhandled/unknown type
                        yield msg.data

        except aiohttp.ClientConnectionError as cce:
            print(f" {cce} !!! Running client interrupted, restarting...")
            await asyncio.sleep(2)

            # recurse here to maintain connection in *same control flow*.
            async for m in self.__aiter__():
                yield m

            # TODO: save subscriptions and resubscribe automatically...


    # async def __call__(self, on_text=None, on_error=None, on_other=None):
    #     await self.session_create()
    #
    #     # TODO : handle connection/websocket errors here
    #     try:
    #         async with session.ws_connect(self.websocket_url) as conn:
    #             self.connection = conn
    #             async for msg in self.connection:  # REF:https://docs.kraken.com/websockets/#info
    #                 if msg.type == aiohttp.WSMsgType.TEXT:
    #
    #                     # to avoid flying blind we first need to parse json into python
    #                     data = json.loads(msg.data)
    #                     if on_text is None:
    #                         LOGGER.info(f'{data}')
    #                     else:
    #                         on_text(data)
    #
    #                 # TODO : protocol exceptions !!
    #                 elif msg.type == aiohttp.WSMsgType.ERROR:
    #                     if on_error is None:
    #                         LOGGER.error(f'{msg}')
    #                         LOGGER.error(f'{msg.type}')
    #                         LOGGER.error(f'{msg.data}')
    #                         break
    #                     else:
    #                         on_error(msg)
    #                 else:
    #                     if on_other is None:
    #                         LOGGER.error(f'{msg}')
    #                         LOGGER.error(f'{msg.type}')
    #                         LOGGER.error(f'{msg.data}')
    #                         break
    #                     else:
    #                         on_other(msg)
    #     # in case internet connection fails try and reconnect automatically after 5 seconds
    #     # there will be no subscriptions though...
    #     except aiohttp.ClientConnectionError:
    #         await asyncio.sleep(5)
    #         print(" !!! Running client interrupted, restarting...")
    #         self._runtask = self.loop.create_task(
    #             self(callback=self.api, connection_name=connection_name, connection_env=connection_env)
    #         )
    #         # TODO: save subscriptions and resubscribe automatically...
    #
    #     self.connection = None

    # TODO : subscribe with @property interface ?? or __getitem__ ?
    async def subscribe(self, subdata: Subscribe):
        """ add new subscription """
        schema = SubscribeSchema()
        strdata = schema.dumps(subdata)

        # TODO : generate a schema based on what we expect ?
        # self._expected_event["subscriptionStatus"] += SubscriptionStatus()

        await self.connection.send_str(strdata)

    async def unsubscribe(self, unsubdata: Unsubscribe):
        """ stops a subscription """
        schema = UnsubscribeSchema()
        strdata = schema.dumps(unsubdata)

        # TODO : generate a schema based on what we expect ?
        # self._expected_event["subscriptionStatus"] += SubscriptionStatus()

        await self.connection.send_str(strdata)

    def __del__(self):
        # if reference disappear, we want to close it !
        if self.connection is not None:
            asyncio.get_running_loop().call_soon(self.connection.close)


if __name__ == '__main__':

    # Note this should be *sync*, cf sans-io
    def message_cb(msg):
        print(f"message_cb: {msg}")

    # Note this should be *sync*, cf sans-io
    def error_cb(msg):
        print(f"error_cb: {msg}")

    async def main():
        try:
            ws = WssConnection(websocket_url="wss://beta-ws.kraken.com")
            ws(aiohttp.WSMsgType.TEXT)(message_cb)
            ws(aiohttp.WSMsgType.ERROR)(error_cb)

            async for msg in ws:
                # non-handled/unknown messages only
                print(f'{msg}')
                print(f'{msg.type}')
                print(f'{msg.data}')

            # TODO : handle protocol errors here...
        except aiohttp.ClientConnectionError as cce:
            print(cce)

    async def mainbis():
        try:
            ws = WssConnection(websocket_url="wss://beta-ws-auth.kraken.com")
            ws(aiohttp.WSMsgType.TEXT)(message_cb)
            ws(aiohttp.WSMsgType.ERROR)(error_cb)

            async for msg in ws:
                # non-handled/unknown messages only
                print(f'{msg}')
                print(f'{msg.type}')
                print(f'{msg.data}')

            # TODO : handle protocol errors here...
        except aiohttp.ClientConnectionError as cce:
            print(cce)

    async def sched():
        await asyncio.gather(main(), mainbis())

    asyncio.run(sched())
