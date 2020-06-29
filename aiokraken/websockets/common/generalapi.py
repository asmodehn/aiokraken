import asyncio
import json
from asyncio import Future
from enum import Enum
from typing import Callable

import aiohttp
import typing

from aiokraken.websockets.common.channel import Channel
from aiokraken.websockets.common.substream import SubStream

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe, UnsubscribeSchema

from aiokraken.websockets.schemas.subscribe import Subscribe, SubscribeOne, SubscribeSchema

from aiokraken.websockets.schemas.ohlc import OHLCUpdateSchema

from aiokraken.websockets.schemas.ticker import TickerWSSchema

from aiokraken.websockets.schemas.subscriptionstatus import (
    SubscriptionStatus, SubscriptionStatusError,
    SubscriptionStatusSchema,
)

from aiokraken.websockets.schemas.systemstatus import SystemStatus, SystemStatusSchema

from aiokraken.websockets.schemas.heartbeat import Heartbeat, HeartbeatSchema

from aiokraken.websockets.common.connections import WssConnection



class KrakenEvent(Enum):
    heartbeat= "Heartbeat"
    SystemStatus= "SystemStatus"
    SubscriptionStatus= "SubscriptionStatus"


class API:  # 1 instance per connection

    _future_channels: typing.Dict[SubscribeOne, asyncio.Future]
    _substreams: typing.Dict[int, typing.List[SubStream]]

    def __init__(self, connect):
        self.connect = connect

        self.reqid = 1

        # three things possible when getting a response

        # temporary storage for in-flight requests
        # : typing.Dict
        self._future_channels = dict()

        # we have a channel already setup
        self._substreams = dict()


    # def _text_dispatch(self, message):
    #     if isinstance(message, list):
    #         current = self._channels[message[0]]  # matching by channel id
    #
    #         # we need to verify the match on other criteria
    #         if current.channel_name == message[2] and current.pair == message[3]:
    #             current(message[1])
    #         else:
    #             raise RuntimeWarning(f"message not transmitted to channel: {message}")
    #     elif isinstance(message, dict):
    #         # We can always attempt a match on "event" string and decide on the response schema from it.
    #         if message.get("event") == "heartbeat":
    #             schema = HeartbeatSchema()
    #             data = schema.load(message)
    #             for h in self._handlers["HeartBeat"]:
    #                 h(data)
    #         elif message.get("event") == "systemStatus":
    #             schema = SystemStatusSchema()
    #             data = schema.load(message)
    #             for h in self._handlers["SystemStatus"]:
    #                 h(data)
    #         elif message.get("event") == "subscriptionStatus":
    #             schema = SubscriptionStatusSchema()
    #
    #             data = schema.load(message)
    #
    #             if isinstance(data, SubscriptionStatusError):
    #                 # TODO : better recording of errors
    #                 print(f"ERROR : {data.error_message}")
    #             else:  # normal case
    #                 # based on docs https://docs.kraken.com/websockets/#message-subscriptionStatus
    #                 # we know here we will have:
    #                 pair = data.pair  # the pair
    #                 subname = data.subscription.name  # the subscription name
    #                 # others interesting  are optional (reqid...)
    #
    #                 request = None
    #                 for r in self._response_tracker:  # pick the first match subscription match
    #                     if r.pair == pair and r.subscription.name == subname:
    #                         request = r
    #                         break
    #
    #                 if request is None:
    #                     # This can happen if the request was requested multiple times,
    #                     # but was already processed as part of a ealier reponse
    #                     return  # => early return
    #
    #                 if data.status == 'subscribed':
    #                     # setting up parsers for data
    #
    #                     # TODO: base this on channel name or on subscription data ?
    #                     if data.channel_name == "ticker":
    #                         channel_schema = TickerWSSchema()
    #                     elif data.channel_name.startswith("ohlc"):  # name depends also on interval !
    #                         channel_schema = OHLCUpdateSchema()
    #                     else:
    #                         raise NotImplementedError("unknown channel name. please add it to the code...")
    #
    #                     if data.channel_id not in self._channels:
    #                         # creating channel with registered callback
    #                         chan = Channel(channel_id=data.channel_id,
    #                                        channel_name=data.channel_name,
    #                                        subscribe_request=request,  # TODO: probably subscription is better here ?
    #                                        schema=channel_schema,
    #                                        pair=data.pair,
    #                                        callbacks=self._callbacks[request])
    #                         print(f"Channel created: {chan}")
    #                         # assigning channel to this api.
    #                         self._channels[data.channel_id] = chan
    #                     else:
    #                         # Nothing to do here, multiple identical requests were sent and received the same channel...
    #                         pass  # side-effect: only the first message in the channel will be duplicated
    #                         # TODO : channel does NOT guarantee unicity of a message.
    #
    #                     # We reached this part: our inflight reponse has landed.
    #                     self._response_tracker.remove(request)
    #
    #                 elif data.status == 'unsubscribed':
    #                     raise NotImplementedError  # TODO

    def _error_dispatch(self, msg):
        raise NotImplementedError

    async def pingpong(self):
        # a simple unblocking send ping recv pong
        return

    def _heartbeat_cb(self, msg: Heartbeat):
        # TODO : somehow "expect" a beat at a certain time...
        pass

    def _systemstatus_cb(self, msg: SystemStatus):
        # only keep latest status
        self._status = msg

    def _subscriptionstatus_cb(self, data: typing.Union[SubscriptionStatus, SubscriptionStatusError]):
        if isinstance(data, SubscriptionStatusError):
            # TODO : better recording of errors
            print(f"ERROR : {data.error_message}")
        else:  # normal case
            # based on docs https://docs.kraken.com/websockets/#message-subscriptionStatus
            # we know here we will have:
            pair = data.pair  # the pair (always unique here)
            subname = data.subscription.name  # the subscription name
            # others interesting  are optional (reqid...)

            request = None
            for r in self._future_channels:  # pick the first match subscription match
                if r.subscription.name == subname and pair in r.pair:  # because merging is on pairs...
                    request = r

            if request is None:
                # This can happen if the request was requested multiple times,
                # but was already processed as part of a ealier reponse
                return  # => early return

            if data.status == 'subscribed':
                # setting up parsers for data

                # TODO: base this on channel name or on subscription data ?
                if data.channel_name == "ticker":
                    channel_schema = TickerWSSchema()
                elif data.channel_name.startswith("ohlc"):  # name depends also on interval !
                    channel_schema = OHLCUpdateSchema()
                else:
                    raise NotImplementedError("unknown channel name. please add it to the code...")

                # retrieve potentially existing channelq for this id

                if data.channel_id not in self._substreams:

                    # creating channel
                    chan = Channel(channel_id=data.channel_id,
                                   channel_name=data.channel_name,
                                   schema=channel_schema,
                                   pair=data.pair)
                    print(f"Channel created: {chan}")

                    # We reached this part: our inflight reponse has landed.
                    self._future_channels[request].set_result(chan)

                    # assigning substream to this channel_id. This is done in subscribe,
                    # but we should at least assign one here to be immediately ready to receive messages
                    self._substreams.setdefault(data.channel_id, list())
                    self._substreams[data.channel_id].append(SubStream(channels={chan}))

                else:
                    # Nothing to do here, multiple identical requests were sent and received the same channel...
                    pass  # side-effect: only the first message in the channel will be duplicated
                    # TODO : channel does NOT guarantee unicity of a message.

            elif data.status == 'unsubscribed':
                raise NotImplementedError  # TODO

    # From systemStatus data on connection
    @property
    def id(self):
        try:
            return self._status.connection_id
        except Exception as exc:
            raise exc

    @property
    def version(self):
        try:
            return self._status.version
        except Exception as exc:
            raise exc

    async def subscribe(self, subdata: Subscribe) -> SubStream:
        #  a simple request response API, unblocking.
        """ add new subscription and return a substream, ready to be used as an async iterator """
        schema = SubscribeSchema()

        # Because one request can potentially trigger multiple responses
        # Beware: channel matching with subscription is relying on SubscribeOne equality!
        chans = {reqone: f for reqone, f in self._future_channels.items() if f.done and reqone in subdata}

        for s in subdata:
            if s not in chans:
                # creating one future channel for each missing pair...
                future_channel = asyncio.get_running_loop().create_future()
                self._future_channels[s] = future_channel
            # else:
            #     for req, c in chans.items():
            #         if c.channel_id
            #     self._substreams[c.channel_id].append(c)
        strdata = schema.dumps(subdata)

        # TODO : generate a schema based on what we expect ?
        # self._expected_event["subscriptionStatus"] += SubscriptionStatus()

        await self.connect(strdata)

        # assigning substream to this channel_id.
        substream = SubStream(channels=set())
        for s in subdata:
            channel = await self._future_channels[s]
            # aggregating into substream
            for ss in self._substreams[channel.channel_id]:
                substream = substream + ss

        for cid in substream.channel_ids:
            self._substreams[cid].append(substream)

        # TODO : merging substreams with different channel_ids...
        #  => need to register itself into the api's substreams ??

        return substream

    async def unsubscribe(self, unsubdata: Unsubscribe):
        #  a simple request response API, unblocking.
        """ stops a subscription """
        schema = UnsubscribeSchema()

        strdata = schema.dumps(unsubdata)

        # TODO : generate a schema based on what we expect ?
        # self._expected_event["subscriptionStatus"] += SubscriptionStatus()

        await self.connect.send_str(strdata)


    async def __aiter__(self):

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

                chan_id = message[0]

                matching = None
                if chan_id in self._substreams:
                    matching = self._substreams[message[0]]  # matching by channel id
                # TODO : maybe leverage marshmallow for channel/msg matching ??
                if not matching:
                    raise RuntimeWarning(f"WARNING !! Message not transmitted to channel: {message}")
                else:
                    for m in matching:  # potentially duplicating message to make sure all receive it
                        # we need to verify the match on other criteria
                        if message[2] in m.channel_name and message[3] in m.pairs:
                            await m(message[1])

            elif isinstance(message, dict):
                # We can always attempt a match on "event" string and decide on the response schema from it.
                if message.get("event") == "heartbeat":
                    schema = HeartbeatSchema()
                    data = schema.load(message)
                    self._heartbeat_cb(data)
                elif message.get("event") == "systemStatus":
                    schema = SystemStatusSchema()
                    data = schema.load(message)
                    self._systemstatus_cb(data)
                elif message.get("event") == "subscriptionStatus":
                    schema = SubscriptionStatusSchema()
                    data = schema.load(message)
                    self._subscriptionstatus_cb(data)
                else:
                    # unknown message type
                    yield message
            else:
                raise NotImplementedError


if __name__ == '__main__':

    async def main():
        api = API(WssConnection("wss://beta-ws.kraken.com"))

        # @api.SystemStatus()
        # def systemstatus(sysstatus):
        #     print(f"SystemStatus: {sysstatus}")

        async for msg in api:
            # unknown message only end up here
            print(msg)

    asyncio.run(main())

