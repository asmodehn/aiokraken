import asyncio
import contextlib
import inspect
import json
from dataclasses import dataclass

import aiohttp
import typing

from aiokraken.websockets.exceptions import AIOKrakenWebSocketError
from aiokraken.websockets.session import unified_session_context

from aiokraken.websockets.schemas.subscribe import Subscribe

from aiokraken.utils import get_kraken_logger

LOGGER = get_kraken_logger(__name__)


class WssConnection:  # instance per URL !
    websocket_url: str  # TODO : more precise type
    connection: typing.Optional[aiohttp.ClientWebSocketResponse]

    # the whole point of this class : track subscriptions by connection...
    subscribed: typing.List[Subscribe]

    def __init__(self, websocket_url):
        self.websocket_url = websocket_url
        self.connection = None
        self._handlers = dict()

    async def __call__(self, data) -> None:
        # sending data (async)
        while self.connection is None:
            await asyncio.sleep(0.2)  # busy wait until we are connected ( by consuming messages)
        LOGGER.warning(f"wss >> {data}")
        await self.connection.send_str(data)

    async def __aiter__(self):
        # receiving data (async)
        # TODO : add static counter to count reentrency and fail before too deep recursion...

        async with unified_session_context() as session:

            # TODO : handle connection/websocket errors here
            #  to provide sticky connection (and linearization of messages for a given protocol)...
            try:
                # Reconnect reference : https://github.com/aaugustin/websockets/issues/414
                async with session.ws_connect(self.websocket_url) as conn:
                    self.connection = conn

                    async for msg in self.connection:  # REF:https://docs.kraken.com/websockets/#info

                        if msg.type == aiohttp.WSMsgType.ERROR:
                            # we manage errors via exceptions (as usual in python),
                            # but careful about eventloop exception handling...
                            raise AIOKrakenWebSocketError(msg.data)
                        elif msg.type == aiohttp.WSMsgType.TEXT:
                            # pattern match on the value of an enum...
                            LOGGER.warning(f"wss << {msg.data}")
                            yield msg.data
                        else:  # unhandled/unknown type
                            # TODO : implement websocket management stuff here
                            raise NotImplementedError(msg)

            # TODO Handle all websocket / aiohttp connection issues here.
            #  Protocol, ie WsMsgType.ERROR will be handled in client code.
            except aiohttp.ClientConnectionError as cce:
                print(f" {cce} !!! Running client interrupted, restarting...")
                await asyncio.sleep(2)

                # recurse here to maintain connection in *same control flow*.
                async for m in self.__aiter__():
                    yield m

                # TODO: save subscriptions and resubscribe automatically...
            except Exception as e:
                print(e)
                raise


if __name__ == '__main__':

    async def main():
        try:
            ws = WssConnection(websocket_url="wss://beta-ws.kraken.com")

            async for msg in ws:
                print(f"message_cb: {msg}")

        except Exception as exc:
            print(exc)

    async def mainbis():
        try:
            ws = WssConnection(websocket_url="wss://beta-ws-auth.kraken.com")

            async for msg in ws:
                print(f"Message Data: {msg}")

        except Exception as exc:
            raise exc

    async def sched():
        await asyncio.gather(main(),
                             mainbis(),
                             )

    try:
        asyncio.run(sched(), debug=True)
    except KeyboardInterrupt as ki:
        print("Done.")
