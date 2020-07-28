
# NOTE : The API / Client couple here is DUAL to rest (because most of it is callback, not callforward)
#  => the API is what the user should use directly (and not the client like for REST)
import asyncio

import typing

from aiokraken.rest import AssetPairs

from aiokraken.websockets.channelstream import SubStream

from aiokraken.websockets.channelsubscribe import (
    PublicChannelSet, public_subscribe, public_subscribed,
    public_unsubscribe,
)

from aiokraken.utils import get_kraken_logger

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe, UnsubscribeSchema

from aiokraken.websockets.connections import WssConnection
from aiokraken.websockets.generalapi import API


from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription, SubscribeOne

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscriptionstatus import (
    SubscriptionStatusError,
)

# TODO : careful, it seems that exceptions are not forwarded to the top process
#  but somehow get lost into the event loop... needs investigation...

LOGGER = get_kraken_logger(__name__)

public_connection = WssConnection(websocket_url="wss://beta-ws.kraken.com")


# Notice: get inspiration from PrivateAPI as it is simpler than the public one
class PublicAPI(API):

    # not channels here have one more level of indirection than privateAPI,
    # to effectively take care of the "pair/id" level...

    def __init__(self, connect: WssConnection):
        super(PublicAPI, self).__init__(connect=connect)

    async def subscribe(self, pairs: typing.Iterable[AssetPair], subscription: Subscription, reqid: int) -> SubStream:
        #  a simple request response API, unblocking.
        """ add new subscription and return a substream, ready to be used as an async iterator """

        # Because one request can potentially trigger multiple responses
        # Beware: channel matching with subscription is relying on SubscribeOne equality!
        # check which pair we should subscribe to (not already subscribed)

        # creates necessary futures expecting request/response
        subdata, chanset = public_subscribe(pairs=AssetPairs({p.wsname: p for p in pairs}),
                                            subscription=subscription,
                                            loop=asyncio.get_running_loop(), reqid=reqid)

        if subdata:
            # we use the exact same subdata here
            strdata = self.subscribe_schema.dumps(subdata)
            await self.connect(strdata)

        # retrieving all channel_ids for this subscription:

        self._streams[subdata] = SubStream(channelset=chanset, pairs=AssetPairs({p.wsname: p for p in pairs}))

        return await self._streams[subdata]
        # TODO : maybe context manager to cleanup the queue when we dont use it or unsubscribe ?

    async def unsubscribe(self, pairs: typing.Iterable[AssetPair], subscription: Subscription, reqid: int):
        #  a simple request response API, unblocking.
        """ stops a subscription """

        unsubdata, chan = public_unsubscribe(pairs=AssetPairs({p.wsname: p for p in pairs}),
                            subscription=subscription,
                            reqid=reqid)
        if unsubdata:
            strdata = self.unsubscribe_schema.dumps(unsubdata)
            await self.connect(strdata)

        # TODO : some return or finalization of some kind ?

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
                        public_subscribed(channel_id=data.channel_id,
                                          channel_name=data.channel_name,
                                          pairstr=data.pair)

                    elif data.status == 'unsubscribed':
                        raise NotImplementedError  # TODO

            else:
                # unknown message type
                yield message


_publicapi = PublicAPI(public_connection)

reqid = 0

msgpull_task = None


def msgpull():
    """ Runs a unique background task to receive messages, even if not explicitly requested by the user"""
    async def unknown():
        async for msg in _publicapi:  # required to consume messages...
            print(f"Unknown message: {msg}")  # TODO : probaby onto some error log somehow...

    if msgpull_task is None:
        asyncio.get_running_loop().create_task(unknown())


async def ticker(pairs: typing.List[typing.Union[AssetPair, str]], restclient = None):
    global reqid, public_connection

    # we need to depend on restclient for usability TODO : unicity : we just need to import it here...
    pairs = [(await restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

    reqid += 1  # leveraging reqid to recognize response

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgpull()

    msgqueue = await _publicapi.subscribe(
        pairs=pairs,
        subscription=Subscription(name="ticker"),
        reqid=reqid)

    await msgqueue  # awaiting al subscription to be set.

    async for msg in msgqueue:
        yield msg


# TODO : KTimeFrameModel instead of int as interval
async def ohlc(pairs: typing.List[typing.Union[AssetPair, str]], interval: int = 1, restclient=None):
    global reqid, public_connection

    # we need to depend on restclient for usability TODO : unicity : we just need to import it here...
    pairs = [(await restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

    reqid += 1  # leveraging reqid to recognize response

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgpull()

    msgqueue = await _publicapi.subscribe(
        pairs=pairs,
        subscription=Subscription(name="ohlc", interval=interval),
        reqid=reqid
    )

    await msgqueue  # awaiting al subscription to be set.

    async for msg in msgqueue:
        yield msg


async def trade(pairs: typing.List[typing.Union[AssetPair, str]], restclient=None):
    global reqid, public_connection

    # we need to depend on restclient for usability TODO : unicity : we just need to import it here...
    pairs = [(await restclient.assetpairs)[p] if isinstance(p, str) else p for p in pairs] if pairs else []

    reqid += 1  # leveraging reqid to recognize response

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgpull()

    msgqueue = await _publicapi.subscribe(
        pairs=pairs,
        subscription=Subscription(name="trade"),
        reqid=reqid
    )

    await msgqueue  # awaiting al subscription to be set.

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


    async def tkr_connect1():
        # async for msg in ticker([xtz_eur_pair], restclient=client):
        async for msg in ticker([xtz_eur_pair, eth_eur_pair], restclient=client):
            print(f"wss ==> ticker xtz eth: {msg}")

    async def tkr_connect2():
        async for msg in ticker([xbt_eur_pair, xtz_eur_pair], restclient=client):
            print(f"wss ==> ticker xbt xtz: {msg}")

    async def sched():
        print(f"Ticker for {xtz_eur_pair} and {eth_eur_pair}")
        await asyncio.gather(
            tkr_connect1(),
            tkr_connect2(),  # Note how xtz messages only should be duplicated in output...
        )

    # async def ohlc_connect1():
    #     # async for msg in ticker([xtz_eur_pair], restclient=client):
    #     async for msg in ohlc([xtz_eur_pair, eth_eur_pair], restclient=client):
    #         print(f"wss ==> ohlc xtz eth: {msg}")
    #
    # async def ohlc_connect2():
    #     async for msg in ohlc([xbt_eur_pair, xtz_eur_pair], restclient=client):
    #         print(f"wss ==> ohlc xbt xtz: {msg}")
    #
    # async def sched():
    #     print(f"OHLC for {xtz_eur_pair} and {eth_eur_pair}")
    #     await asyncio.gather(
    #         ohlc_connect1(),
    #         ohlc_connect2(),  # Note how xtz messages only should be duplicated in output...
    #     )

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
    #     )

    asyncio.run(sched())





