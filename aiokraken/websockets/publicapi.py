
# NOTE : The API / Client couple here is DUAL to rest (because most of it is callback, not callforward)
#  => the API is what the user should use directly (and not the client like for REST)
import asyncio

import typing

from aiokraken.websockets.substream import PublicSubStream
from aiokraken.websockets.schemas.unsubscribe import Unsubscribe, UnsubscribeSchema

from aiokraken.websockets.channel import channel
from aiokraken.websockets.connections import WssConnection
from aiokraken.websockets.generalapi import API


from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription, SubscribeOne

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscriptionstatus import (
    SubscriptionStatusError,
)

# TODO : careful, it seems that exceptions are not forwarded to the top process
#  but somehow get lost into the event loop... needs investigation...


public_connection = WssConnection(websocket_url="wss://beta-ws.kraken.com")

# Notice: get inspiration from PrivateAPI as it is simpler than the public one
class PublicAPI(API):

    # not channels here have one more level of indirection than privateAPI,
    # to effectively take care of the "pair/id" level...
    _future_channels: typing.Dict[str, typing.Dict[str, asyncio.Future]]

    def __init__(self, connect: WssConnection):
        super(PublicAPI, self).__init__(connect=connect)

        self._future_channels = dict()

    async def subscribe(self, subdata: Subscribe) -> PublicSubStream:
        #  a simple request response API, unblocking.
        """ add new subscription and return a substream, ready to be used as an async iterator """

        # Because one request can potentially trigger multiple responses
        # Beware: channel matching with subscription is relying on SubscribeOne equality!
        # check which pair we should subscribe to (not already subscribed)

        # relative to this subscription name, these are the available pairs
        available_pairs = set()

        # creating a dict to store a channel for each requested pair if needed
        # CAREFUL with special naming...
        if subdata.subscription.name == "ohlc":
            subname = f"ohlc-{subdata.subscription.interval}"
        else:
            subname = subdata.subscription.name
        self._future_channels.setdefault(subname, dict())

        for pair in self._future_channels[subname].keys():
            available_pairs.add(pair)

        subscribe_required_pairs = subdata.pair - available_pairs

        if subscribe_required_pairs:
            # if we don't have a channel with this name and pair yet, we need to actually subscribe
            for p in subscribe_required_pairs:
                self._future_channels[subname][p] = asyncio.get_running_loop().create_future()

            # we use the exact same subdata here
            strdata = self.subscribe_schema.dumps(
                Subscribe(subscription=subdata.subscription,
                          pair=subscribe_required_pairs,
                          reqid=subdata.reqid)
            )

            await self.connect(strdata)

        # awaiting all channels and building the subscribe stream
        stream = PublicSubStream(* [await self._future_channels[subname][p] for p in subdata.pair])

        # storing the stream for this subscribe request
        self._streams[subdata] = stream
        # TODO : maybe the whole subdata instead of just the name ???

        return stream  # TODO : maybe context manager to cleanup the queue when we dont use it or unsubscribe ?

    async def unsubscribe(self, unsubdata: Unsubscribe):
        #  a simple request response API, unblocking.
        """ stops a subscription """
        schema = UnsubscribeSchema()

        strdata = schema.dumps(unsubdata)

        # TODO : generate a schema based on what we expect ?
        # self._expected_event["subscriptionStatus"] += SubscriptionStatus()

        await self.connect(strdata)

    async def __aiter__(self):
        async for message in super(PublicAPI, self).__aiter__():
            # only retrieves message not handled by super
            if message.get("event") == "subscriptionStatus":
                data = self.publicsubscriptionstatus_schema.load(message)

                if isinstance(data, SubscriptionStatusError):
                    # TODO : better recording of errors
                    print(f"ERROR : {data.error_message}")
                else:  # normal case
                    # based on docs https://docs.kraken.com/websockets/#message-subscriptionStatus
                    if data.status == 'subscribed':
                        # setting up channels for data
                        chan = channel(name=data.channel_name,
                                       # public channel needs pair and id as well
                                       pair=data.pair, id=data.channel_id)

                        # new subscribed event : we set (or replace existing) channel
                        self._future_channels[chan.channel_name][data.pair].set_result(chan)

                        print(f"Channel created: {chan}")

                        # retrieve potentially existing channels for this id

                    elif data.status == 'unsubscribed':
                        raise NotImplementedError  # TODO

            else:
                # unknown message type
                yield message


_publicapi = PublicAPI(public_connection)

reqid = 0


async def ticker(pairs: typing.List[typing.Union[AssetPair, str]], restclient = None):
    global reqid, public_connection

    # we need to depend on restclient for usability TODO : unicity : we just need to import it here...
    pairs = [(await restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

    reqid += 1  # leveraging reqid to recognize response
    subdata = Subscribe(pair =[p.wsname for p in pairs], subscription=Subscription(name="ticker"), reqid=reqid)

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgqueue = await _publicapi.subscribe(subdata)

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

    msgqueue = await _publicapi.subscribe(subdata)

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

    msgqueue = await _publicapi.subscribe(subdata)

    async for msg in msgqueue:
        yield msg


async def spread(pairs: typing.List[typing.Union[AssetPair, str]], restclient=None):
    raise NotImplementedError("DO IT !")


async def book(pairs: typing.List[typing.Union[AssetPair, str]], restclient=None):
    raise NotImplementedError("DO IT !")

if __name__ == '__main__':
    from aiokraken.rest.client import RestClient
    client = RestClient()
    xtz_eur_pair = "XTZ/EUR"
    eth_eur_pair = "ETH/EUR"
    xbt_eur_pair = "XBT/EUR"

    async def other():
        async for msg in _publicapi:  # required to consume messages...
            print(f"Another message: {msg}")

    #
    # async def tkr_connect1():
    #     # async for msg in ticker([xtz_eur_pair], restclient=client):
    #     async for msg in ticker([xtz_eur_pair, eth_eur_pair], restclient=client):
    #         print(f"wss ==> ticker xtz eth: {msg}")
    #
    # async def tkr_connect2():
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

    async def ohlc_connect1():
        # async for msg in ticker([xtz_eur_pair], restclient=client):
        async for msg in ohlc([xtz_eur_pair, eth_eur_pair], restclient=client):
            print(f"wss ==> ohlc xtz eth: {msg}")

    async def ohlc_connect2():
        async for msg in ohlc([xbt_eur_pair, xtz_eur_pair], restclient=client):
            print(f"wss ==> ohlc xbt xtz: {msg}")

    async def sched():
        print(f"OHLC for {xtz_eur_pair} and {eth_eur_pair}")
        await asyncio.gather(
            ohlc_connect1(),
            ohlc_connect2(),  # Note how xtz messages only should be duplicated in output...
            other()
        )

    #
    # async def trade_connect1():
    #     # async for msg in ticker([xtz_eur_pair], restclient=client):
    #     async for msg in trade([xtz_eur_pair, eth_eur_pair], restclient=client):
    #         print(f"wss ==> trade xtz eth: {msg}")
    #
    # async def trade_connect2():
    #     async for msg in trade([xbt_eur_pair, xtz_eur_pair], restclient=client):
    #         print(f"wss ==> trade xbt xtz: {msg}")
    #
    # async def sched():
    #     print(f"Trades for {xbt_eur_pair}, {xtz_eur_pair} and {eth_eur_pair}")
    #     await asyncio.gather(
    #         trade_connect1(),
    #         trade_connect2(),  # Note how xtz messages only should be duplicated in output...
    #         other()
    #     )

    asyncio.run(sched())





