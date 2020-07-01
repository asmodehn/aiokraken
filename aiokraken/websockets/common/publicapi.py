
# NOTE : The API / Client couple here is DUAL to rest (because most of it is callback, not callforward)
#  => the API is what the user should use directly (and not the client like for REST)
import asyncio
import inspect

import typing
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass

from aiokraken.rest.schemas.base import BaseSchema
from aiokraken.websockets.common.connections import WssConnection
from aiokraken.websockets.common.generalapi import API

from aiokraken.websockets.schemas.heartbeat import Heartbeat, HeartbeatSchema

from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy
from aiokraken.websockets.schemas.ohlc import OHLCUpdateSchema
from aiokraken.websockets.schemas.pingpong import Ping

from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription, SubscribeOne

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

from aiokraken.websockets.channel import Channel

from aiokraken.websockets.schemas.subscriptionstatus import (
    SubscriptionStatusSchema, SubscriptionStatus,
    SubscriptionStatusError,
)

from aiokraken.websockets.schemas.systemstatus import SystemStatusSchema, SystemStatus

# TODO : careful, it seems that exceptions are not forwarded to the top process
#  but somehow get lost into the event loop... needs investigation...


# class WSAPI:
#     """
#     API help describe the websocket interface.
#     It deals with the model and schemas, and also manages message channels.
#     """
#
#     def __init__(self, heartbeat_cb: typing.Callable, systemStatus_cb: typing.Callable):
#
#         # setting the heartbeat callback to connect optional client behavior
#         self._heartbeat = heartbeat_cb
#         self._system_status = systemStatus_cb
#
#         self.reqid = 1
#
#         # three things possible when getting a response
#
#         # temporary storage for in-flight requests
#         self._response_tracker = set()
#
#         # we need to add a callback
#         self._callbacks = dict()
#
#         # we have a channel already setup
#         self._channels = dict()
#
#     def __call__(self, message):
#         if isinstance(message, list):
#             current = self._channels[message[0]]  # matching by channel id
#
#             # we need to verify the match on other criteria
#             if current.channel_name == message[2] and current.pair == message[3]:
#                 current(message[1])
#             else:
#                 raise RuntimeWarning(f"message not transmitted to channel: {message}")
#
#         elif isinstance(message, dict):
#             # We can always attempt a match on "event" string and decide on the response schema from it.
#             # TODO : or maybe manage these first 2 directly in the client ?
#             if message.get("event") == "heartbeat":
#                 schema = HeartbeatSchema()
#                 data = schema.load(message)
#                 self._heartbeat(data)
#             elif message.get("event") == "systemStatus":
#                 schema = SystemStatusSchema()
#                 data = schema.load(message)
#                 self._system_status(data)
#             elif message.get("event") == "subscriptionStatus":
#                 schema = SubscriptionStatusSchema()
#
#                 data = schema.load(message)
#
#                 if isinstance(data, SubscriptionStatusError):
#                     # TODO : better recording of errors
#                     print(f"ERROR : {data.error_message}")
#                 else:  # normal case
#                     # based on docs https://docs.kraken.com/websockets/#message-subscriptionStatus
#                     # we know here we will have:
#                     pair = data.pair  # the pair
#                     subname = data.subscription.name  # the subscription name
#                     # others interesting  are optional (reqid...)
#
#                     request = None
#                     for r in self._response_tracker:  # pick the first match subscription match
#                         if r.pair == pair and r.subscription.name == subname:
#                             request = r
#                             break
#
#                     if request is None:
#                         # This can happen if the request was requested multiple times,
#                         # but was already processed as part of a ealier reponse
#                         return  # => early return
#
#                     if data.status == 'subscribed':
#                         # setting up parsers for data
#
#                         # TODO: base this on channel name or on subscription data ?
#                         if data.channel_name == "ticker":
#                             channel_schema = TickerWSSchema()
#                         elif data.channel_name.startswith("ohlc"):  # name depends also on interval !
#                             channel_schema = OHLCUpdateSchema()
#                         else:
#                             raise NotImplementedError("unknown channel name. please add it to the code...")
#
#                         if data.channel_id not in self._channels:
#                             # creating channel with registered callback
#                             chan = Channel(channel_id=data.channel_id,
#                                            channel_name=data.channel_name,
#                                            subscribe_request=request,  # TODO: probably subscription is better here ?
#                                            schema=channel_schema,
#                                            pair=data.pair,
#                                            callbacks=self._callbacks[request])
#                             print(f"Channel created: {chan}")
#                             # assigning channel to this api.
#                             self._channels[data.channel_id] = chan
#                         else:
#                             # Nothing to do here, multiple identical requests were sent and received the same channel...
#                             pass  # side-effect: only the first message in the channel will be duplicated
#                             # TODO : channel does NOT guarantee unicity of a message.
#
#                         # We reached this part: our inflight reponse has landed.
#                         self._response_tracker.remove(request)
#
#                     elif data.status == 'unsubscribed':
#                         raise NotImplementedError  # TODO
#
#             else:
#                 raise RuntimeError("unknown message type.")
#
#
#     def ping(self, callback):
#         self.reqid +=1
#         pingdata = Ping(reqid=self.reqid)
#         self.ping_callback = callback
#         return pingdata
#
#     def ticker(self, pairs: typing.List[AssetPair], callback: typing.Callable) -> typing.Optional[Subscribe]:
#         self.reqid += 1  # leveraging reqid to recognize response
#         subdata = Subscribe(pair =[p.wsname for p in pairs], subscription=Subscription(name="ticker"), reqid=self.reqid)
#
#         # Because one request can trigger multiple responses
#         for s in subdata:
#             # Beware: channel matching with subscription is relying on Subscribe equality!
#             chans = {c.subscribe_request: c for id, c in self._channels.items() if c.subscribe_request == s}
#             if chans:
#                 for c in chans:
#                     # just add callback to existing channel
#                     c.callbacks.append(callback)
#                 return  # return early with no request to be made
#             else:
#                 # adding inflight response
#                 self._response_tracker.add(s)
#
#                 # request to get a new subscription and create a chan
#                 self._callbacks.setdefault(s, [])
#                 self._callbacks[s].append(callback)
#                 # callback by subscription data, waiting for channel open message...
#
#             return subdata  # the channel expected name
#
#     def ohlc(self, pairs: typing.List[AssetPair], callback: typing.Callable, interval: int = 1) -> typing.Optional[Subscribe]:
#         self.reqid += 1  # leveraging reqid to recognize response
#         print(f"Subscribing to {[p.wsname for p in pairs]} ")
#         subdata = Subscribe(pair=[p.wsname for p in pairs],  subscription=Subscription(name="ohlc", interval=interval), reqid=self.reqid)
#
#         # Because one request can potentially trigger multiple responses
#         for s in subdata:
#             # Beware: channel matching with subscription is relying on SubscribeOne equality!
#             chans = {c.subscribe_request: c for id, c in self._channels.items() if c.subscribe_request == s}
#             if chans:
#                 for c in chans.values():
#                     # just add callback to existing channel
#                     c.callbacks.append(callback)
#                 return  # return early with no request to be made
#             else:
#                 # adding inflight response
#                 self._response_tracker.add(s)
#
#                 # request to get a new subscription and create a chan
#                 self._callbacks.setdefault(s, [])
#                 self._callbacks[s].append(callback)
#                 # callback by subscription data, waiting for channel open message...
#
#         return subdata
#
#     def trades(self, callback: typing.Callable, token: typing.Optional[str]) -> typing.Optional[Subscribe]:
#         self.reqid += 1  # leveraging reqid to recognize response
#
#         if token is None:  # TODO : is this  agood idea ? how about two different APIs ?
#             # TODO : subscribe to get all trades
#             raise NotImplementedError
#         else:
#             # only get my own trades
#
#             print(f"Subscribing to ownTrades")
#             subdata = Subscribe(subscription=Subscription(name="ownTrades", token="bob"),
#                                 reqid=self.reqid)
#
#         # Because one request can potentially trigger multiple responses
#         for s in subdata:
#             # Beware: channel matching with subscription is relying on SubscribeOne equality!
#             chans = {c.subscribe_request: c for id, c in self._channels.items() if c.subscribe_request == s}
#             if chans:
#                 for c in chans.values():
#                     # just add callback to existing channel
#                     c.callbacks.append(callback)
#                 return  # return early with no request to be made
#             else:
#                 # adding inflight response
#                 self._response_tracker.add(s)
#
#                 # request to get a new subscription and create a chan
#                 self._callbacks.setdefault(s, [])
#                 self._callbacks[s].append(callback)
#                 # callback by subscription data, waiting for channel open message...
#
#         return subdata


public_connection = WssConnection(websocket_url="wss://beta-ws.kraken.com")

general_api = API(public_connection)

reqid = 0


async def ticker(pairs: typing.List[typing.Union[AssetPair, str]], restclient = None):
    global reqid, public_connection

    # we need to depend on restclient for usability TODO : unicity : we just need to import it here...
    pairs = [(await restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

    reqid += 1  # leveraging reqid to recognize response
    subdata = Subscribe(pair =[p.wsname for p in pairs], subscription=Subscription(name="ticker"), reqid=reqid)

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgqueue = await general_api.subscribe(subdata)

    async for msg in msgqueue:
        yield msg


async def  ohlc(pairs: typing.List[typing.Union[AssetPair, str]], interval: int = 1, restclient=None):
    global reqid, public_connection

    # we need to depend on restclient for usability TODO : unicity : we just need to import it here...
    pairs = [(await restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

    reqid += 1  # leveraging reqid to recognize response
    subdata = Subscribe(pair =[p.wsname for p in pairs], subscription=Subscription(name="ohlc", interval=interval), reqid=reqid)

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgqueue = await general_api.subscribe(subdata)

    async for msg in msgqueue:
        yield msg


async def trade(pairs: typing.List[typing.Union[AssetPair, str]], restclient=None):
    global reqid, public_connection

    # we need to depend on restclient for usability TODO : unicity : we just need to import it here...
    pairs = [(await restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

    reqid += 1  # leveraging reqid to recognize response
    subdata = Subscribe(pair =[p.wsname for p in pairs], subscription=Subscription(name="trade"), reqid=reqid)

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgqueue = await general_api.subscribe(subdata)

    async for msg in msgqueue:
        yield msg


if __name__ == '__main__':
    from aiokraken.rest.client import RestClient
    client = RestClient()
    xtz_eur_pair = "XTZ/EUR"
    eth_eur_pair = "ETH/EUR"
    xbt_eur_pair = "XBT/EUR"

    async def other():
        async for msg in general_api:  # required to consume messages...
            print(f"Another message: {msg}")

    #
    # async def tkr_connect1():
    #     # async for msg in ticker([xtz_eur_pair], restclient=client):
    #     async for msg in ticker([xtz_eur_pair, eth_eur_pair], restclient=client):
    #         print(f"wss ==> ticker xtz eth: {msg}")
    #
    # async def tkr_connect2():
    #     # async for msg in ticker([xtz_eur_pair], restclient=client):
    #     async for msg in ticker([xbt_eur_pair, xtz_eur_pair], restclient=client):
    #         print(f"wss ==> ticker xbt xtz: {msg}")
    #
    # async def sched():
    # print(f"Ticker for {xtz_eur_pair} and {eth_eur_pair}")
    #     await asyncio.gather(
    #         tkr_connect1(),
    #         tkr_connect2(),  # Note how xtz messages only should be duplicated in output...
    #         other()
    #     )

    # async def ohlc_connect1():
    #     # async for msg in ticker([xtz_eur_pair], restclient=client):
    #     async for msg in ohlc([xtz_eur_pair, eth_eur_pair], restclient=client):
    #         print(f"wss ==> ohlc xtz eth: {msg}")
    #
    # async def ohlc_connect2():
    #     # async for msg in ticker([xtz_eur_pair], restclient=client):
    #     async for msg in ohlc([xbt_eur_pair, xtz_eur_pair], restclient=client):
    #         print(f"wss ==> ohlc xbt xtz: {msg}")
    #
    # async def sched():
    #     print(f"OHLC for {xtz_eur_pair} and {eth_eur_pair}")
    #     await asyncio.gather(
    #         ohlc_connect1(),
    #         ohlc_connect2(),  # Note how xtz messages only should be duplicated in output...
    #         other()
    #     )


    async def trade_connect1():
        # async for msg in ticker([xtz_eur_pair], restclient=client):
        async for msg in trade([xtz_eur_pair, eth_eur_pair], restclient=client):
            print(f"wss ==> trade xtz eth: {msg}")

    async def trade_connect2():
        # async for msg in ticker([xtz_eur_pair], restclient=client):
        async for msg in trade([xbt_eur_pair, xtz_eur_pair], restclient=client):
            print(f"wss ==> trade xbt xtz: {msg}")

    async def sched():
        print(f"Trades for {xtz_eur_pair} and {eth_eur_pair}")
        await asyncio.gather(
            trade_connect1(),
            trade_connect2(),  # Note how xtz messages only should be duplicated in output...
            other()
        )

    asyncio.run(sched())





