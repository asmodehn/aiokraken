from __future__ import annotations

# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc
import asyncio
from dataclasses import dataclass, field

import typing

from aiokraken.websockets.schemas.owntrades import ownTradeWSSchema

from aiokraken.websockets.schemas.trade import TradeWSSchema

from aiokraken.websockets.schemas.ohlc import OHLCUpdateSchema

from aiokraken.websockets.schemas.ticker import TickerWSSchema

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscribe import Subscribe

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema


PairChannelId = typing.NamedTuple("PairChannelId", [("pair", AssetPair), ("channel_id", int)])


@dataclass(frozen=True, init=False)
class SubStream:
    """
    A channel, called when a message is received.
    Behaves as a stream, enqueueing messages until iteration is performed to consume them.

    Note : this can assemble a set of kraken channel ids in order to linearize their messages
     in only one async generator, based on subscription request.
    """
    pairs_channel_ids: typing.Set[PairChannelId]
    # Important : given kraken WS API design, we have one pair per channel
    # BUT one user can subscribe to multiple pairs at once, and needs to aggregate channels here.

    @property
    def pairs(self):
        return set(p for p, cid in self.pairs_channel_ids)

    @property
    def channel_ids(self):
        return set(cid for p, cid in self.pairs_channel_ids)

    channel_name: str
    schema: BaseSchema

    queue: asyncio.Queue = field(hash=False)

    def __init__(self,
                 *channels
                 ):

        pair_id_set = {PairChannelId(pair=c.pair, channel_id=c.id) for c in channels}
        schema_set = {c.schema for c in channels}
        name_set = {c.channel_name for c in channels}

        # TODO : with types / schemas ?
        assert len(schema_set) == 1
        assert len(name_set) == 1

        object.__setattr__(self, 'pairs_channel_ids', pair_id_set )

        object.__setattr__(self, 'channel_name', next(iter(name_set)))
        object.__setattr__(self, 'schema', next(iter(schema_set)))

        object.__setattr__(self, 'queue', asyncio.Queue(maxsize=8))  # to quickly trigger exception if no consumer setup.

    # SINK

    async def __call__(self, message) -> None:

        # structure of a message on a public channel :
        # - https://docs.kraken.com/websockets-beta/#message-ticker
        # - https://docs.kraken.com/websockets-beta/#message-ohlc
        # - https://docs.kraken.com/websockets-beta/#message-trade
        # - https://docs.kraken.com/websockets-beta/#message-spread
        # - https://docs.kraken.com/websockets-beta/#message-book

        chan_id = message[0]
        data = message[1]
        channel = message[2]
        pair = message[3]

        if channel == self.channel_name and chan_id in self.channel_ids and pair in self.pairs:
            # also calling the parsed model to store the pair here as well...
            parsed = self.schema.load(data)
            # this is specific to public streams
            parsed_with_pair = parsed(pair)
            await self.queue.put(parsed_with_pair)
        # otherwise nothing happens

    ## SOURCE

    async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
        while self.queue:
            yield await self.queue.get()
            self.queue.task_done()
