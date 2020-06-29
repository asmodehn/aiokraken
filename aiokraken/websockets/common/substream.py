from __future__ import annotations

import asyncio
from asyncio import QueueEmpty
from dataclasses import dataclass, field


# TODO : make a 1-1 relationship in request / channel, to make it functional and linear.
import typing

from aiokraken.rest.schemas.base import BaseSchema

from aiokraken.model.assetpair import AssetPair

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException
from aiokraken.websockets.common.channel import Channel


@dataclass()
class SubStream:
    """
    A subscription stream

    Note : this can assemble a set of kraken channel ids in order to linearize their messages
     in only one async generator, based on subscription request.

     Substream and Channel interfaces are similar, but not identical, as they are used in slightly different contexts.
    """

    ## container
    channels: typing.Set[Channel]

    @property
    def pairs(self):
        return set(c.pair for c in self.channels)

    @property
    def channel_ids(self):
        return set(c.channel_id for c in self.channels)

    # Should be unique -> maybe not a set ? how to ensure it ?
    @property
    def channel_name(self):
        chnm = set(c.channel_name for c in self.channels)
        assert len(chnm) in [0,1]
        return chnm

    # Should be unique -> maybe not a set ? how to ensure it ?
    @property
    def schema(self):
        schm = set(c.schema for c in self.channels)
        assert len(schm) in [0,1]
        return schm

    queue: asyncio.Queue = field(default_factory=asyncio.Queue, hash=False)

    # @property
    # def qsize(self):
    #     return self.queue.qsize()
    # YAGNI

    # SINK

    async def __call__(self, data):
        for s in self.schema:
            try:
                parsed = s.load(data)
                await self.queue.put(parsed)
                break  # first successful parsing wins
            except AIOKrakenSchemaValidationException as aiosve:  # TODO : check if actually needed ?
                if isinstance(data, list) and len(data) == len(s.declared_fields):
                    data_dict = dict()
                    # attempt again by iterating on fields
                    for f, d in zip(s.declared_fields.keys(), data):
                        data_dict[f] = d
                    parsed = s.load(data_dict)
                    await self.queue.put(parsed)
        else:
            raise AIOKrakenSchemaValidationException(f" No schema could parse {data}")

    ## SOURCE

    async def __aiter__(self):
        while self.queue:
            yield await self.queue.get()
            self.queue.task_done()

    ## container

    def __getitem__(self, item: AssetPair):

        # TODO : various ways to get a sublist...
        # Think containers...

        return SubStream(
            channels=set(c for c in self.channels if c.pair == item.wsname),
        )

    def __add__(self, other: SubStream):  # TODO : mul ??
        # immutable style => duplication of data

        assert len(self.channel_name.union(other.channel_name)) == 1, "cannot merge substreams with different channel name"
        assert len(self.schema.union(other.schema)) == 1, "cannot merge substream with different schema"

        merged = SubStream(
            channels=self.channels | other.channels,
        )

        return merged
