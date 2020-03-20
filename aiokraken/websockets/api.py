
# NOTE : The API / Client couple here is DUAL to rest (because most of it is callback, not callforward)
#  => the API is what the user should use directly (and not the client like for REST)
import asyncio
import inspect

import typing

from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.ticker import TickerWS, TickerWSSchema

from aiokraken.websockets.channel import Channel

from aiokraken.websockets.schemas.subscriptionstatus import SubscriptionStatusSchema, SubscriptionStatus

from aiokraken.websockets.schemas.systemstatus import SystemStatusSchema, SystemStatus



class WSAPI:

    def __init__(self):
        self._callbacks = dict()

        self._channels = dict()

    def __call__(self, message):
        current = self._channels[message[0]]  # matching by channel id

        # we need to verify the match on other criteria
        if current.channel_name == message[2] and current.pair == message[3]:
            current(message[1])




    # def _callback(self, message):
    #     # generic "all events" method, dispatching to others
    #     if isinstance(message, dict):
    #         if message.get('event') == 'subscriptionStatus':
    #             print(f"subscription status : {message}")  # TODO : manage errors here
    #         elif message.get('event') == 'systemStatus':
    #             print(f'system status: {message}')
    #         else:
    #             print(f"unprocessed message {message}")
    #     else:  # IDEA : heartbeat is a specific event that should trigger ALL callbacks, so that the user knows
    #         #        its final callback is "connected", ie "eventually callable"
    #         print(f'unexpected message {message}')
    #         ts = TickerSchema()
    #         tkr = ts.load(data=message)
    #         self._callbacks["ticker"](tkr=tkr)

    # Special API:

    async def heartbeat(self):
        pass

    def subscriptionStatus(self, message: SubscriptionStatus):
        if message.status == 'subscribed':
            # setting up parsers for data
            if message.channel_name == "ticker":
                channel_schema = TickerWSSchema()
            else:
                raise NotImplementedError("unknown channel name. please add it to the code...")

            chan = Channel(channel_id=message.channel_id,
                           channel_name=message.channel_name,
                           schema=channel_schema,
                           pair=message.pair,
                           callbacks=[self._callbacks[message.channel_name]])
            self._channels[message.channel_id] = chan
            return chan  # we return channel so the client can finally register callbacks in there...
        else:
            raise RuntimeError("unhandled subscription status")

    def systemStatus(self, message: SystemStatus):
        return message  # nothing to do here (maybe internal to the client ?)

    def ticker(self, pairs: typing.List[AssetPair], callback: typing.Callable) -> Subscribe:
        # TODO : maybe we should accumulate the pair names here ?
        subdata = Subscribe(pair =[p.wsname for p in pairs], subscription=Subscription(name="ticker"))

        self._callbacks["ticker"] = callback  # callback by expected channel name, waiting for channel open message...

        # TODO : maybe do something to expect the subscription callback ?
        return subdata  # the channel expected name


    #
    # def ticker(self, pairs, connection_name = "main"):
    #     """ subscribe to the ticker update stream.
    #     if the returned wrapper is not used, the message will still be parsed,
    #     until the appropriate wrapper (stored in _callbacks) is called.
    #     """
    #     self.subt = self.loop.create_task(self.client.subscribe(pairs=pairs, subscription={
    #             "name": 'ticker'
    #         }, connection_name=connection_name))
    #
    #     @wrapt.decorator
    #     def wrapper(wrapped, instance, args, kwargs):
    #         # called on message received
    #         wrapped(*args, **kwargs)
    #
    #     self._callbacks["ticker"] = wrapper
    #
    #     return wrapper

    # TODO : or maybe via generator ??? (cf design of timecontrol, and final user interface concepts...)
    #  Note: we should keep the buffer behavior for the input and outputs of the whole process
    #  => no buffer 'inside' for simplicity.


if __name__ == '__main__':
    wsapi = WSAPI()

    wsapi.ticker()






