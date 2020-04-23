
# NOTE : The API / Client couple here is DUAL to rest (because most of it is callback, not callforward)
#  => the API is what the user should use directly (and not the client like for REST)
import asyncio
import inspect

import typing
from collections import Mapping, MutableMapping
from dataclasses import dataclass

from aiokraken.rest.schemas.base import BaseSchema

from aiokraken.websockets.schemas.heartbeat import Heartbeat, HeartbeatSchema

from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy
from aiokraken.websockets.schemas.ohlc import OHLCUpdateSchema
from aiokraken.websockets.schemas.pingpong import Ping

from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription, SubscribeOne

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

from aiokraken.websockets.channel import Channel

from aiokraken.websockets.schemas.subscriptionstatus import SubscriptionStatusSchema, SubscriptionStatus

from aiokraken.websockets.schemas.systemstatus import SystemStatusSchema, SystemStatus

# TODO : careful, it seems that exceptions are not forwarded to the top process
#  but somehow get lost into the event loop... needs investigation...


class WSAPI:
    """
    API help describe the websocket interface.
    It deals with the model and schemas, and also manages message channels.
    """

    def __init__(self, heartbeat_cb: typing.Callable, systemStatus_cb: typing.Callable):

        # setting the heartbeat callback to connect optional client behavior
        self._heartbeat = heartbeat_cb
        self._system_status = systemStatus_cb

        self.reqid = 1

        # three things possible when getting a response

        # temporary storage for in-flight requests
        self._response_tracker = set()

        # we need to add a callback
        self._callbacks = dict()

        # we have a channel already setup
        self._channels = dict()

    def __call__(self, message):
        if isinstance(message, list):
            current = self._channels[message[0]]  # matching by channel id

            # we need to verify the match on other criteria
            if current.channel_name == message[2] and current.pair == message[3]:
                current(message[1])
            else:
                raise RuntimeWarning(f"message not transmitted to channel: {message}")

        elif isinstance(message, dict):
            # We can always attempt a match on "event" string and decide on the response schema from it.
            # TODO : or maybe manage these first 2 directly in the client ?
            if message.get("event") == "heartbeat":
                schema = HeartbeatSchema()
                data = schema.load(message)
                self._heartbeat(data)
            elif message.get("event") == "systemStatus":
                schema = SystemStatusSchema()
                data = schema.load(message)
                self._system_status(data)
            elif message.get("event") == "subscriptionStatus":
                schema = SubscriptionStatusSchema()

                data = schema.load(message)

                # based on docs https://docs.kraken.com/websockets/#message-subscriptionStatus
                # we know here we will have:
                pair = data.pair  # the pair
                subname = data.subscription.name  # the subscription name
                # others interesting  are optional (reqid...)

                request = None
                for r in self._response_tracker:  # pick the first match subscription match
                    if r.pair == pair and r.subscription.name == subname:
                        request = r
                        break

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

                    if data.channel_id not in self._channels:
                        # creating channel with registered callback
                        chan = Channel(channel_id=data.channel_id,
                                       channel_name=data.channel_name,
                                       subscribe_request=request,  # TODO: probably subscription is better here ?
                                       schema=channel_schema,
                                       pair=data.pair,
                                       callbacks=self._callbacks[request])
                        print(f"Channel created: {chan}")
                        # assigning channel to this api.
                        self._channels[data.channel_id] = chan
                    else:
                        # Nothing to do here, multiple identical requests were sent and received the same channel...
                        pass  # side-effect: only the first message in the channel will be duplicated
                        # TODO : channel does NOT guarantee unicity of a message.

                    # We reached this part: our inflight reponse has landed.
                    self._response_tracker.remove(request)

                elif data.status == 'unsubscribed':
                    raise NotImplementedError  # TODO

            else:
                raise RuntimeError("unknown message type.")


    def ping(self, callback):
        self.reqid +=1
        pingdata = Ping(reqid=self.reqid)
        self.ping_callback = callback
        return pingdata

    def ticker(self, pairs: typing.List[AssetPair], callback: typing.Callable) -> typing.Optional[Subscribe]:
        self.reqid += 1  # leveraging reqid to recognize response
        subdata = Subscribe(pair =[p.wsname for p in pairs], subscription=Subscription(name="ticker"), reqid=self.reqid)

        # Because one request can trigger multiple responses
        for s in subdata:
            # Beware: channel matching with subscription is relying on Subscribe equality!
            chans = {c.subscribe_request: c for id, c in self._channels.items() if c.subscribe_request == s}
            if chans:
                for c in chans:
                    # just add callback to existing channel
                    c.callbacks.append(callback)
                return  # return early with no request to be made
            else:
                # adding inflight response
                self._response_tracker.add(s)

                # request to get a new subscription and create a chan
                self._callbacks.setdefault(s, [])
                self._callbacks[s].append(callback)
                # callback by subscription data, waiting for channel open message...

            return subdata  # the channel expected name

    def ohlc(self, pairs: typing.List[AssetPair], callback: typing.Callable, interval: int = 1) -> typing.Optional[Subscribe]:
        self.reqid += 1  # leveraging reqid to recognize response
        subdata = Subscribe(pair=[p.wsname for p in pairs],  subscription=Subscription(name="ohlc", interval=interval), reqid=self.reqid)

        # Because one request can potentially trigger multiple responses
        for s in subdata:
            # Beware: channel matching with subscription is relying on SubscribeOne equality!
            chans = {c.subscribe_request: c for id, c in self._channels.items() if c.subscribe_request == s}
            if chans:
                for c in chans:
                    # just add callback to existing channel
                    c.callbacks.append(callback)
                return  # return early with no request to be made
            else:
                # adding inflight response
                self._response_tracker.add(s)

                # request to get a new subscription and create a chan
                self._callbacks.setdefault(s, [])
                self._callbacks[s].append(callback)
                # callback by subscription data, waiting for channel open message...

            return subdata


if __name__ == '__main__':

    def hb(msg):
        print(msg)

    def sysst(msg):
        print(msg)

    # creating WSAPI with heartbeat callback
    wsapi = WSAPI(heartbeat_cb=hb, systemStatus_cb=sysst)

    print(wsapi.ping(callback= lambda x: x))

    print(wsapi.ticker([AssetPairStrategy().example()], callback= lambda x: x))

    print(wsapi.ohlc([AssetPairStrategy().example(), AssetPairStrategy().example()], callback= lambda x: x))





