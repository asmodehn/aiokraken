from __future__ import annotations

# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc
import asyncio
from dataclasses import dataclass, field

import typing

from aiokraken.websockets.channel import PrivateChannel, PublicChannel

from aiokraken.model.assetpair import AssetPair


PairChannelId = typing.NamedTuple("PairChannelId", [("pair", AssetPair), ("channel_id", int)])


@dataclass(frozen=True, init=False)
class PublicSubStream:
    """
    A channel, called when a message is received.
    Behaves as a stream, enqueueing messages until iteration is performed to consume them.

    Note : this can assemble a set of kraken channel ids in order to linearize their messages
     in only one async generator, based on subscription request.
    """

    channel: PublicChannel
    pairs: typing.Set[AssetPair]  # This is the set of pairs we subscribed to at once (a subset of entire known channel pairs)
    queue: asyncio.Queue = field(hash=False)

    def __init__(self,
                 channel,
                 pairs
                 ):

        object.__setattr__(self, 'channel', channel)
        object.__setattr__(self, 'pairs', pairs)
        object.__setattr__(self, 'queue', asyncio.Queue(maxsize=8))  # to quickly trigger exception if no consumer setup.

    # SINK

    async def __call__(self, chan_id, data, channel, pair) -> None:
        # Here we only filter in the pairs we are interested in.
        if channel == self.channel.channel_name and pair in self.pairs:
            # parsing message ignoring errors
            if parsed := self.channel(chan_id, data, channel, pair):
                await self.queue.put(parsed.value)
        # otherwise nothing happens

    ## SOURCE

    async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
        while self.queue:
            yield await self.queue.get()
            self.queue.task_done()


@dataclass(frozen=True, init=False)
class PrivateSubStream:
    """
    A channel, called when a message is received.
    Behaves as a stream, enqueueing messages until iteration is performed to consume them.

    Note : this can assemble a set of kraken channel ids in order to linearize their messages
     in only one async generator, based on subscription request.
    """

    channel: PrivateChannel

    queue: asyncio.Queue = field(hash=False)

    def __init__(self,
                 channel
                 ):

        object.__setattr__(self, 'channel', channel)

        object.__setattr__(self, 'queue', asyncio.Queue(maxsize=8))  # to quickly trigger exception if no consumer setup.

    # SINK

    async def __call__(self, data, channel) -> None:
        if channel == self.channel.channel_name:
            # parsing message ignoring errors
            if parsed := self.channel(data, channel):
                await self.queue.put(parsed.value)
        # otherwise nothing happens

    ## SOURCE

    async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
        while self.queue:
            yield await self.queue.get()
            self.queue.task_done()
