import asyncio
import functools
import itertools
from types import MappingProxyType

import typing

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe

from aiokraken.rest import AssetPairs

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.channelparser import privatechannelparser, publicchannelparser


class PublicChannelSet:

    subids: typing.Dict[AssetPair, asyncio.Future]
    parsers: typing.Dict[int, typing.Callable]

    def __init__(self):
        self.subids = dict()
        self.parsers = dict()

    def __contains__(self, item: typing.Union[AssetPair, int]):
        return item in self.subids.keys() or item in self.parsers.keys()

    def __getitem__(self, item: typing.Union[AssetPair, int]):
        if isinstance(item, AssetPair):
            return self.subids[item]
        elif isinstance(item, int):
            return self.parsers[item]
        else:
            raise KeyError(f"{item}")

    def subscribe(self, *, pairs: AssetPairs, loop: asyncio.AbstractEventLoop) -> AssetPairs:
        """ create futures as needed and return the ones that we should expect"""
        subpairs = {}
        for p in pairs.values():
            if p not in self.subids:
                self.subids[p] = loop.create_future()
                subpairs[p.wsname]=p
        return AssetPairs(assetpairs_as_dict=subpairs)

    def unsubscribe(self, *, pairs: AssetPairs) -> AssetPairs:
        subpairs = {}
        for p in pairs.values():
            if p in self.subids:
                self.subids.pop(p)  # just dropping channel id future
                subpairs[p.wsname]=p
        return AssetPairs(assetpairs_as_dict=subpairs)

    def subscribed(self, *, channel_name: str, pairstr: str, channel_id: int) -> None:
        for ap in self.subids.keys():
            if ap.wsname == pairstr:
                # TMP
                # if self.subids[ap].done():
                #     print(self.subids[ap])
                break
        else:
            # received a subscribed event for something we didnt subscribe to ?
            raise RuntimeWarning(f" Unexpected Subscription: {channel_name} {pairstr} {channel_id}")
        assert pairstr == ap.wsname

        self.parsers[channel_id] = functools.partial(publicchannelparser(channel_name=channel_name), pair=ap)

        # TMP
        # if self.subids[ap].done():
        #     print(self.subids[ap])
        assert not self.subids[ap].done()
        # signal channel is ready to receive message by setting the subscribed future
        self.subids[ap].set_result(channel_id)

    def __call__(self, *, chan_id, data, pair: str) -> typing.Any:  # TODO : refine Any ?
        # parsing data received
        return self.parsers[chan_id](data=data)
        # Note here we trust the assetpair <-> channel_id relationship we set previously on subscribed()


# Note we have to store object here so that we can forward them somewhere else to be mutated...
# (probably not a good idea BTW ?) TODO : some different, more easily testable design ?
trade: PublicChannelSet = PublicChannelSet()
ticker: PublicChannelSet = PublicChannelSet()
ohlc: typing.Dict[int, PublicChannelSet] = {  # TODO : refine int to KTimeFrameModel
    tf.value: PublicChannelSet()
    for tf in KTimeFrameModel
}


def public_subscribe(pairs: AssetPairs, subscription: Subscription, loop: asyncio.AbstractEventLoop,
                     reqid: typing.Optional[int] = None) -> typing.Tuple[typing.Optional[Subscribe], PublicChannelSet]:
    # for subscription request
    global trade, ticker, ohlc
    if subscription.name == "trade":
        subpairs = trade.subscribe(pairs=pairs, loop=loop)

        subdata = Subscribe(pair=[p.wsname for p in subpairs.values()],
                         subscription=subscription,
                         reqid=reqid) if subpairs else None
        return subdata, trade

    elif subscription.name == "ticker":
        subpairs = ticker.subscribe(pairs=pairs, loop=loop)

        subdata = Subscribe(pair=[p.wsname for p in subpairs.values()],
                         subscription=subscription,
                         reqid=reqid) if subpairs else None
        return subdata, ticker

    elif subscription.name == "ohlc":
        ohlc_chan = subscription_channel(subscription)

        subpairs = ohlc_chan.subscribe(pairs=pairs, loop=loop)

        subdata = Subscribe(pair=[p.wsname for p in subpairs.values()],
                         subscription=subscription,
                         reqid=reqid) if subpairs else None
        return subdata, ohlc_chan

    else:
        raise NotImplementedError


def public_subscribed(channel_name: str, pairstr: str, channel_id: int) -> PublicChannelSet:
    # on subscribed received
    if channel_name == "trade":
        trade.subscribed(channel_name=channel_name, pairstr=pairstr, channel_id=channel_id)
        return trade
    elif channel_name == "ticker":
        ticker.subscribed(channel_name=channel_name, pairstr=pairstr, channel_id=channel_id)
        return ticker
    elif channel_name.startswith("ohlc"):
        sub = channel_name_subscription(channel_name)
        chan = subscription_channel(sub)
        chan.subscribed(channel_name=channel_name, pairstr=pairstr, channel_id=channel_id)
        return chan
    else:
        raise NotImplementedError


def public_unsubscribe(pairs: AssetPairs, subscription: Subscription, # loop: asyncio.AbstractEventLoop,  # do we need hte loop to expec the confirmation ??
                     reqid: typing.Optional[int] = None) -> typing.Tuple[typing.Optional[Unsubscribe], PublicChannelSet]:
    # for subscription request
    global trade, ticker
    if subscription.name == "trade":
        subpairs = trade.unsubscribe(pairs=pairs)

        return Unsubscribe(pair=[p.wsname for p in subpairs.values()],
                         subscription=subscription,
                         reqid=reqid), trade

    elif subscription.name == "ticker":
        subpairs = ticker.unsubscribe(pairs=pairs)

        return Unsubscribe(pair=[p.wsname for p in subpairs.values()],
                         subscription=subscription,
                         reqid=reqid), ticker

    elif subscription.name.startswith("ohlc"):
        chan = subscription_channel(subscription)
        subpairs = chan.unsubscribe(pairs=pairs)

        return Unsubscribe(pair=[p.wsname for p in subpairs.values()],
                           subscription=subscription,
                           reqid=reqid), chan
    else:
        raise NotImplementedError


def subscription_channel(subscription: Subscription):
    if subscription.name in ["trade", "ticker"]:
        return globals()[subscription.name]
    elif subscription.name == "ohlc":
        # creating the timeframe key if needed
        return globals()[subscription.name][subscription.interval]
    else:
        raise NotImplementedError


def subscription_channel_name(subscription: Subscription):
    if subscription.name == "trade":
        return "trade"
    elif subscription.name == "ticker":
        return "ticker"
    elif subscription.name == "ohlc":
        return f"ohlc-{subscription.interval}"
    elif subscription.name == "ownTrades":
        return "ownTrades"
    elif subscription.name == "openOrders":
        return "openOrders"
    else:
        raise NotImplementedError


def channel_name_subscription(channel_name):
    if channel_name in ["trade", "ticker", "ownTrades", "openOrders"]:
        return Subscription(name=channel_name)
    elif channel_name.startswith("ohlc"):
        return Subscription(name="ohlc", interval=int(channel_name[5:]))
    else:
        raise NotImplementedError


class ChannelPrivate:

    subid: typing.Optional[asyncio.Future] = None
    parser: typing.Optional[typing.Callable] = None

    def subscribe(self, loop: asyncio.AbstractEventLoop):
        if self.subid is None:
            self.subid = loop.create_future()

    def subscribed(self, *, channel_name: str) -> None:
        self.parser = privatechannelparser(channel_name=channel_name)
        # signal channel is ready to receive message by setting the subscribed future
        self.subid.set_result(channel_name)  # need to set the future to something...

    def unsubscribe(self):
        self.subid = None

    def __call__(self, *, data) -> typing.Any:  # TODO : refine Any ?
        # parsing data received
        return self.parser(data=data)


ownTrades: ChannelPrivate = ChannelPrivate()
openOrders: ChannelPrivate = ChannelPrivate()


# TODO : unify apis : channel_name -> subscription ?
def private_subscribe(channel_name, loop: asyncio.AbstractEventLoop) -> ChannelPrivate:  # TODO : async or not ? eventloop must be same as for private_subscribed()
    global ownTrades, openOrders
    if channel_name == "ownTrades":
        ownTrades.subscribe(loop=loop)
        return ownTrades
    elif channel_name == "openOrders":
        openOrders.subscribe(loop=loop)
        return openOrders
    else:
        raise NotImplementedError(f"{channel_name} is not implemented for private_subscribe. Ignored.")


def private_unsubscribe(channel_name) -> ChannelPrivate:
    global ownTrades, openOrders
    if channel_name == "ownTrades":
        ownTrades.unsubscribe()
        return ownTrades
    elif channel_name == "openOrders":
        openOrders.unsubscribe()
        return openOrders
    else:
        raise NotImplementedError(f"{channel_name} is not implemented for private_unsubscribe. Ignored.")


def private_subscribed(channel_name) -> ChannelPrivate:
    if channel_name == "ownTrades":
        ownTrades.subscribed(channel_name=channel_name)
        return ownTrades
    elif channel_name == "openOrders":
        openOrders.subscribed(channel_name=channel_name)
        return openOrders
    else:
        raise NotImplementedError(f"{channel_name} is not implemented for private_subscribed. Ignored.")


if __name__ == '__main__':
    raise NotImplementedError
