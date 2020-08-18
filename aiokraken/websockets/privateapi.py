
# NOTE : The API / Client couple here is DUAL to rest (because most of it is callback, not callforward)
#  => the API is what the user should use directly (and not the client like for REST)
import asyncio
import typing

from aiokraken.websockets.channelstream import SubStreamPrivate

from aiokraken.websockets.channelsubscribe import private_subscribe, private_subscribed, private_unsubscribe

from aiokraken.utils import get_kraken_logger

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

    def __init__(self, connect: WssConnection):
        super(PrivateAPI, self).__init__(connect=connect)

    async def subscribe(self, subscription: Subscription, reqid: int) -> SubStreamPrivate:
        #  a simple request response API, unblocking.
        """ add new subscription and return a substream, ready to be used as an async iterator """

        # Because subscribe is callable multiple times with the same subdata,
        # but this would trigger "already subscribed" error on kraken side

        chanpriv = private_subscribe(channel_name=subscription.name,
                                            loop=asyncio.get_running_loop())

        subdata = Subscribe(subscription=subscription, reqid=reqid)

        strdata = self.subscribe_schema.dumps(subdata)
        await self.connect(strdata)

        # retrieving all channel_ids for this subscription:

        self._streams[subdata] = SubStreamPrivate(channelprivate=chanpriv)

        # await subscription to be set before returning
        return await self._streams[subdata]
        # TODO : maybe context manager to cleanup the queue when we dont use it or unsubscribe ?

    async def unsubscribe(self, subscription: Subscription):
        #  a simple request response API, unblocking.
        """ stops a subscription """

        private_unsubscribe(channel_name=subscription.name)
        unsubdata = Unsubscribe(subscription=subscription, pair = [])  # TODO : FIX pair ?
        if unsubdata:
            strdata = self.unsubscribe_schema.dumps(unsubdata)
            await self.connect(strdata)

        # TODO : some return or finalization of some kind ?

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

                    if data.status == 'subscribed':
                        # setting up channels for data
                        chan = private_subscribed(channel_name=data.channel_name)

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

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgpull()

    msgqueue = await _privateapi.subscribe(subscription=Subscription(name="ownTrades", token=token), reqid=reqid)

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

    # Note : queue is maybe more internal / lowlevel, keeping the linearity of data. BETTER FIT here when subscribing !
    #        callback implies possible multiplicity (many callbacks => duplication of data).

    msgpull()

    msgqueue = await _privateapi.subscribe(subscription=Subscription(name="openOrders", token=token), reqid=reqid)

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
