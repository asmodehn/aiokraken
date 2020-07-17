import asyncio
import json
from asyncio import Future
from enum import Enum
from typing import Callable

import aiohttp
import typing

from aiokraken.utils import get_kraken_logger

from aiokraken.websockets.substream import PrivateSubStream, PublicSubStream

from aiokraken.websockets.schemas.pingpong import PingSchema, PongSchema


from aiokraken.websockets.schemas.unsubscribe import UnsubscribeSchema

from aiokraken.websockets.schemas.subscribe import Subscribe, SubscribeSchema


from aiokraken.websockets.schemas.subscriptionstatus import (
    PrivateSubscriptionStatusSchema, PublicSubscriptionStatusSchema,
    )

from aiokraken.websockets.schemas.systemstatus import SystemStatus, SystemStatusSchema

from aiokraken.websockets.schemas.heartbeat import Heartbeat, HeartbeatSchema

from aiokraken.websockets.connections import WssConnection


LOGGER = get_kraken_logger(__name__)


class KrakenEvent(Enum):
    heartbeat= "Heartbeat"
    SystemStatus= "SystemStatus"
    SubscriptionStatus= "SubscriptionStatus"


class API:  # 1 instance per connection

    # storing a set of stream for each subscription name
    _streams: typing.Dict[Subscribe, typing.Union[PrivateSubStream,PublicSubStream]]

    # because we need to have only one schema instance that we can reuse multiple times
    subscribe_schema = SubscribeSchema()

    heartbeat_schema = HeartbeatSchema()
    ping_schema = PingSchema()
    pong_schema = PongSchema()
    systemstatus_schema = SystemStatusSchema()
    privatesubscriptionstatus_schema = PrivateSubscriptionStatusSchema()
    publicsubscriptionstatus_schema = PublicSubscriptionStatusSchema()
    unsubscribe_schema = UnsubscribeSchema()

    def __init__(self, connect: WssConnection):
        self.connect = connect

        self.reqid = 1

        self._status = None

        self.heartbeat_queue = None

        self.pong_futures = dict()  # no ordering, just an identifier using reqid.

        self._streams = dict()

    def _error_dispatch(self, msg):
        raise NotImplementedError

    async def pingpong(self):
        self.reqid += 1
        ping = self.ping_schema.load(data={'reqid': self.reqid})

        self.pong_futures[self.reqid] = asyncio.get_running_loop().create_future()

        # send ping when ready
        await self.connect(self.ping_schema.dumps(ping))

        pong = await self.pong_futures[self.reqid]

        return self.pong_schema.dumps(pong)  # returning original message (after parsing and reserializing)

    def _heartbeat_cb(self, msg: Heartbeat):
        # TODO : somehow "expect" a beat at a certain time...
        pass

    async def heartbeat(self):

        while self.heartbeat_queue is None:
            await asyncio.sleep(.2)
            # we are stuck in the inner loop while queue is there (and loop is existing)...
            while self.heartbeat_queue is not None:  # TODO which temrination condition ??
                hb_msg = await self.heartbeat_queue.get()
                yield hb_msg

    def _systemstatus_cb(self, msg: SystemStatus):
        # only keep latest status
        self._status = msg


    # From systemStatus data on connection
    @property
    def id(self):
        try:
            if self._status is None:
                return "???"
            return self._status.connection_id
        except Exception as exc:
            raise exc

    @property
    def version(self):
        try:
            if self._status is None:
                return "???"
            return self._status.version
        except Exception as exc:
            raise exc

    async def __aiter__(self):

        # loop started, we can now create a queue for heartbeat
        self.heartbeat_queue = asyncio.Queue()

        # putting text message receive in place
        # self.connect.WSMsgText(self._text_dispatch)
        # TODO :only deal with text messages here...
        # pulling data, linearized...
        async for message in self.connect:

            # parsing json string
            message = json.loads(message)
            # print(f" DEBUG msg : {message}")

            # only receiving unknowns here but mandatory to pull data...
            if isinstance(message, list):
                for subdata, strm in self._streams.items():
                    # each stream is responsible to drop the message if it is not for itself.
                    await strm(message)

            elif isinstance(message, dict):
                # We can always attempt a match on "event" string and decide on the response schema from it.
                if message.get("event") == "heartbeat":  # TODO : these as async generator methods to have a more transparent API for the user.
                    data = self.heartbeat_schema.load(message)
                    await self.heartbeat_queue.put(data)
                elif message.get("event") == "pong":
                    data = self.pong_schema.load(message)
                    self.pong_futures[data.reqid].set_result(data)
                elif message.get("event") == "systemStatus":
                    data = self.systemstatus_schema.load(message)
                    self._systemstatus_cb(data)

                # subscription is managed in children classes (private or public)

                else:
                    # unknown message type
                    yield message
            else:
                raise NotImplementedError


if __name__ == '__main__':

    # We need to be careful with instance creation before a loop is available...
    api = API(WssConnection("wss://beta-ws.kraken.com"))

    async def other():
        async for msg in api:  # required to consume messages...
            print(f"Another message: {msg}")

    async def watch_heartbeat():
        async for msg in api.heartbeat():
            print(f"heartbeat: {msg}")

    async def periodic_pingpong():
        while not asyncio.get_running_loop().is_closed():
            print(f"PING... ?")
            await api.pingpong()  # result ignored (request/response matching is done by eneralapi)
            print(f"    ...PONG!")
            await asyncio.sleep(5)

    async def passive_systemstatus():
        while not asyncio.get_running_loop().is_closed():
            print(f"SystemStatus: id= {api.id} version= {api.version}")
            await asyncio.sleep(10)

    async def sched():
        await asyncio.gather(
            watch_heartbeat(),
            periodic_pingpong(),
            passive_systemstatus(),
            other()
        )
        # Note : heartbeat may activate only if we have a subscription active... TODO ?

    asyncio.run(sched())
