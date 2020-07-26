import asyncio
import functools
from types import MappingProxyType

import typing

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe

from aiokraken.rest import AssetPairs

from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.websockets.schemas.subscribe import Subscribe, Subscription

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.channelparser import privatechannelparser, publicchannelparser


# class PublicChannel:
#
#     pair: AssetPair
#     subid: asyncio.Future
#     parser: typing.Optional[typing.Callable] = None
#
#     def __init__(self, *, pair: AssetPair, loop):
#         self.pair = pair
#         self.subid = loop.create_future()
#
#     def subscribed(self, *, channel_name: str, pairstr: str, channel_id: int) -> None:
#         assert pairstr == self.pair.wsname
#         self.parser = functools.partial(publicchannelparser(channel_name=channel_name), pair=self.pair)
#         # signal channel is ready to receive message by setting the subscribed future
#         self.subid.set_result(channel_id)
#
#     def __call__(self, *, chan_id, data, pair: str) -> typing.Any:  # TODO : refine Any ?
#         # parsing data received
#         assert chan_id == self.subid.result()  # WARNING: result has to be set here !
#         assert pair == self.pair.wsname
#         return self.parser(data=data)


class PublicChannelSet:

    subids: typing.Dict[AssetPair, asyncio.Future]
    parsers: typing.Dict[int, typing.Callable]

    def __init__(self):
        self.subids = dict()
        self.parsers = dict()

    def __contains__(self, item: AssetPair):
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


trade: typing.Optional[PublicChannelSet] = None
ticker: typing.Optional[PublicChannelSet] = None

for tf in KTimeFrameModel:
    globals()[f'ohlc-{tf.value}'] = None


def public_subscribe(pairs: AssetPairs, subscription: Subscription, loop: asyncio.AbstractEventLoop,
                     reqid: typing.Optional[int] = None) -> typing.Tuple[typing.Optional[Subscribe], PublicChannelSet]:
    # for subscription request
    global trade, ticker
    if subscription.name == "trade":
        if trade is None:
            trade = PublicChannelSet()

        subpairs = trade.subscribe(pairs=pairs, loop=loop)

        return Subscribe(pair=[p.wsname for p in subpairs.values()],
                         subscription=subscription,
                         reqid=reqid), trade

    elif subscription.name == "ticker":
        if ticker is None:
            ticker = PublicChannelSet()
        subpairs = ticker.subscribe(pairs=pairs, loop=loop)

        return Subscribe(pair=[p.wsname for p in subpairs.values()],
                         subscription=subscription,
                         reqid=reqid), ticker

    elif subscription.name == "":
        raise NotImplementedError


def public_subscribed(channel_name: str, pairstr: str, channel_id: int) -> PublicChannelSet:
    # on subscribed received
    if channel_name == "trade":
        trade.subscribed(channel_name=channel_name, pairstr=pairstr, channel_id=channel_id)
        return trade
    elif channel_name == "ticker":
        ticker.subscribed(channel_name=channel_name, pairstr=pairstr, channel_id=channel_id)
        return ticker
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

    elif subscription.name == "":
        raise NotImplementedError


def subscription_channel(subscription: Subscription):
    name = subscription_channel_name(subscription=subscription)
    return globals()[name]


def subscription_channel_name(subscription: Subscription):
    if subscription.name == "trade":
        return "trade"
    elif subscription.name == "ticker":
        return "ticker"
    elif subscription.name == "ohlc":
        return f"ohlc-{subscription.interval}"
    else:
        raise NotImplementedError


class ChannelPrivate:

    subid: asyncio.Future
    parser: typing.Optional[typing.Callable] = None

    def __init__(self, *, loop):
        self.subid = loop.create_future()

    def subscribed(self, *, channel_name: str) -> None:
        self.parser = privatechannelparser(channel_name=channel_name)
        # signal channel is ready to receive message by setting the subscribed future
        self.subid.set_result(channel_name)  # need to set the future to something...

    def __call__(self, *, data) -> typing.Any:  # TODO : refine Any ?
        # parsing data received
        return self.parser(data=data)


ownTrades: typing.Optional[ChannelPrivate] = None
openOrders: typing.Optional[ChannelPrivate] = None


def private_subscribe(channel_name, loop: asyncio.AbstractEventLoop) -> ChannelPrivate:  # TODO : async or not ? eventloop must be same as for private_subscribed()
    global ownTrades, openOrders
    if channel_name == "ownTrades":
        if ownTrades is None:
            ownTrades = ChannelPrivate(loop=loop)
        return ownTrades
    elif channel_name == "openOrders":
        if openOrders is None:
            openOrders = ChannelPrivate(loop=loop)
        return openOrders
    else:
        raise NotImplementedError(f"{channel_name} is not implemented for private_subscribe. Ignored.")


def private_unsubscribe(channel_name) -> None:
    global ownTrades, openOrders
    if channel_name == "ownTrades":
        ownTrades = None
    elif channel_name == "openOrders":
        openOrders = None
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
