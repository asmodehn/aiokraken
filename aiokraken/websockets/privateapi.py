
# NOTE : The API / Client couple here is DUAL to rest (because most of it is callback, not callforward)
#  => the API is what the user should use directly (and not the client like for REST)
import asyncio
import typing

from aiokraken.utils import get_kraken_logger

from aiokraken.websockets.substream import PrivateSubStream

from aiokraken.websockets.channel import channel
from aiokraken.websockets.schemas.unsubscribe import Unsubscribe
from aiokraken.websockets.connections import WssConnection
from aiokraken.websockets.generalapi import API

from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription
from aiokraken.websockets.schemas.subscriptionstatus import (
    SubscriptionStatusError,
)

LOGGER = get_kraken_logger(__name__)

# TODO : careful, it seems that exceptions are not forwarded to the top process
#  but somehow get lost into the event loop... needs investigation...


private_connection = WssConnection(websocket_url="wss://beta-ws-auth.kraken.com")


class PrivateAPI(API):

    _future_channels: typing.Dict[str, asyncio.Future]

    def __init__(self, connect: WssConnection):
        super(PrivateAPI, self).__init__(connect=connect)

        self._future_channels = dict()

    async def subscribe(self, subdata: Subscribe) -> PrivateSubStream:
        #  a simple request response API, unblocking.
        """ add new subscription and return a substream, ready to be used as an async iterator """

        # Because subscribe is callable multiple times with the same subdata,
        # but this would trigger "already subscribed" error on kraken side

        if subdata.subscription.name not in self._future_channels:  # match based on name
            # if we don't have a channel with this name yet, we need to actually subscribe
            self._future_channels[subdata.subscription.name] = asyncio.get_running_loop().create_future()
            # we use the exact same subdata here
            strdata = self.subscribe_schema.dumps(subdata)

            await self.connect(strdata)

        # retrieving channel tor extract messages from it
        # possibly awaiting for channel to be created by the future
        stream = PrivateSubStream(await self._future_channels[subdata.subscription.name])

        # storing the stream for this subscribe request
        self._streams[subdata] = stream
        # TODO : maybe the whole subdata instead of just the name ???

        return stream  # TODO : maybe context manager to cleanup the queue when we dont use it or unsubscribe ?

    async def unsubscribe(self, unsubdata: Unsubscribe):
        #  a simple request response API, unblocking.
        """ stops a subscription """

        if unsubdata.subscription.name in self._future_channels:

            strdata = self.unsubscribe_schema.dumps(unsubdata)

            await self.connect(strdata)

            # TODO : best place to pop from the list of channels ?? here or callback ??

        # else nothing happens...

    async def __aiter__(self):
        async for message in super(PrivateAPI, self).__aiter__():
            # only retrieves message not handled by super
            if message.get("event") == "subscriptionStatus":
                data = self.privatesubscriptionstatus_schema.load(message)

                if isinstance(data, SubscriptionStatusError):
                    # TODO : better recording of errors
                    print(f"ERROR : {data.error_message}")
                else:  # normal case
                    # based on docs https://docs.kraken.com/websockets/#message-subscriptionStatus

                    # First we need to match channel name

                    if data.status == 'subscribed':
                        # setting up channels for data
                        chan = channel(name=data.channel_name)
                        # new subscribed event : we set (or replace existing) channel
                        self._future_channels[chan.channel_name].set_result(chan)

                        print(f"Channel created: {chan}")

                        # retrieve potentially existing channels for this id

                    elif data.status == 'unsubscribed':
                        raise NotImplementedError  # TODO

            else:
                # unknown message type
                yield message


_privateapi = PrivateAPI(private_connection)

reqid = 0

token = None

msgpull_task = None


def msgpull():
    """ Runs a unique background task to receive messages, even if not explicitly requested by the user"""
    async def unknown():
        async for msg in _privateapi:  # required to consume messages...
            print(f"Unknown message: {msg}")  # TODO : probaby onto some error log somehow...

    if msgpull_task is None:
        asyncio.get_running_loop().create_task(unknown())


async def ownTrades( restclient = None):
    # TODO : maybe uniformize the API by adding pairs: typing.List[typing.Union[AssetPair, str]], ?
    #  It is extra work and may be actually not needed ??
    global reqid, token

    if token is None:
        token = await restclient.websockets_token()

    reqid += 1  # leveraging reqid to recognize response
    subdata = Subscribe(subscription=Subscription(name="ownTrades", token=token), reqid=reqid)

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgpull()

    msgqueue = await _privateapi.subscribe(subdata)

    async for msg in msgqueue:
        yield msg

    # Reasons to exit this loop:
    # - unsubscribed from another coroutine
    # - some error ??


async def openOrders (restclient = None):
    # TODO : maybe uniformize the API by adding pairs: typing.List[typing.Union[AssetPair, str]], ?
    #  It is extra work and may be actually not needed ??
    global reqid, token

    if token is None:
        token = await restclient.websockets_token()

    reqid += 1  # leveraging reqid to recognize response
    subdata = Subscribe(subscription=Subscription(name="openOrders", token=token), reqid=reqid)

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgpull()

    msgqueue = await _privateapi.subscribe(subdata)
    # TODO : sometimes we miss the first message here ???
    async for msg in msgqueue:
        yield msg

    # Reasons to exit this loop:
    # - unsubscribed from another coroutine
    # - some error ??


if __name__ == '__main__':
    from aiokraken.config import load_api_keyfile
    from aiokraken.rest.api import Server
    from aiokraken.rest.client import RestClient

    keystruct = load_api_keyfile()
    client = RestClient(server=Server(key=keystruct.get('key'),
                                    secret=keystruct.get('secret')))

    async def owntrades_connect1():
        print(f"My ownTrades: ")
        async for msg in ownTrades(restclient=client):
            print(f"wss ==> ownTrades: {msg}")

    async def openOrders_connect1():
        print(f"My openOrders: ")
        async for msg in openOrders(restclient=client):
            print(f"wss ==> openOrders: {msg}")

    async def sched():
        await asyncio.gather(
            owntrades_connect1(),
            openOrders_connect1()
        )

    asyncio.run(sched(), debug=True)

# TODO testing testing testing...
