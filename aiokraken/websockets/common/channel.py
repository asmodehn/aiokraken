from __future__ import annotations

# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc
import asyncio
from dataclasses import dataclass, field

import typing

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscribe import Subscribe

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema


PairChannelId = typing.NamedTuple("PairChannelId", [("pair", AssetPair), ("channel_id", int)])


@dataclass(frozen=True, init=False)
class Channel:
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
                 pairs_channel_ids: typing.Union[PairChannelId, typing.Set[PairChannelId]],
                 channel_name: str,
                 schema: BaseSchema,
                 ):
        object.__setattr__(self, 'pairs_channel_ids', pairs_channel_ids if isinstance(pairs_channel_ids, set) else {pairs_channel_ids})
        # set() constructor is idempotent as function or unhashable as data !

        object.__setattr__(self, 'channel_name', channel_name)
        object.__setattr__(self, 'schema', schema)
        object.__setattr__(self, 'queue', asyncio.Queue())

    # SINK

    async def __call__(self, pair, data) -> None:
        # also calling the parsed model to store the pair here as well...
        parsed = self.schema.load(data)(pair)
        await self.queue.put(parsed)


    ## SOURCE

    async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
        while self.queue:
            yield await self.queue.get()
            self.queue.task_done()

    ## container
    # NOT NEEDED -> TODO get rid of it YAGNI.
    # def __getitem__(self, item: AssetPair):
    #
    #     # TODO : various ways to get a sublist...
    #     # Think containers...
    #
    #     if item in self.pairs:
    #         for pcid in self.pairs_channel_ids:
    #             if pcid.pair == item:
    #                 return Channel(
    #                     pairs_channel_ids=set(pcid),
    #                     channel_name=self.channel_name,
    #                     schema=self.schema,
    #                 )
    #         # TODO : what about the queue ??
    #     else:
    #         raise KeyError(f"{item} not in {self.pairs}")

    # NOT NEEDED -> TODO get rid of it YAGNI.
    # def __add__(self, other: Channel):  # TODO : mul ??
    #     # immutable style => duplication of data
    #
    #     assert self.channel_name == other.channel_name == 1, "cannot merge substreams with different channel name"
    #     assert self.schema == other.schema == 1, "cannot merge substream with different schema"
    #
    #     merged = Channel(
    #         pairs_channel_ids=self.pairs_channel_ids | other.pairs_channel_ids,
    #         channel_name=self.channel_name,
    #         schema=self.schema,
    #     )
    #
    #     return merged


if __name__ == '__main__':
    raise NotImplementedError