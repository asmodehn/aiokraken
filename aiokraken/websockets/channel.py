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


@dataclass(frozen=True, init=True)
class PublicChannel:
    pair: str
    id: int
    channel_name: str
    schema: BaseSchema

    # async def __call__(self, message) -> None:
    #
    #     # structure of a message on a public channel :
    #     # - https://docs.kraken.com/websockets-beta/#message-ticker
    #     # - https://docs.kraken.com/websockets-beta/#message-ohlc
    #     # - https://docs.kraken.com/websockets-beta/#message-trade
    #     # - https://docs.kraken.com/websockets-beta/#message-spread
    #     # - https://docs.kraken.com/websockets-beta/#message-book
    #
    #     chan_id = message[0]
    #     data = message[1]
    #     channel = message[2]
    #     pair = message[3]
    #
    #     if channel == self.channel_name and chan_id in self.channel_ids and pair in self.pairs:
    #         # also calling the parsed model to store the pair here as well...
    #         parsed = self.schema.load(data)(pair)
    #         await self.queue.put(parsed)
    #     # otherwise nothing happens
    #
    #
    # ## SOURCE
    #
    # async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
    #     while self.queue:
    #         yield await self.queue.get()
    #         self.queue.task_done()

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

@dataclass(frozen=True)
class PrivateChannel:
    """
    A channel, called when a message is received.
    Behaves as a stream, enqueueing messages until iteration is performed to consume them.

    Note : this can assemble a set of kraken channel ids in order to linearize their messages
     in only one async generator, based on subscription request.
    """

    channel_name: str
    schema: BaseSchema

    # queue: asyncio.Queue = field(hash=False)
    #
    # def __init__(self,
    #              channel_name: str,
    #              schema: BaseSchema,
    #              ):
    #
    #     object.__setattr__(self, 'channel_name', channel_name)
    #     object.__setattr__(self, 'schema', schema)
    #     object.__setattr__(self, 'queue', asyncio.Queue(maxsize=8))  # to quickly trigger exception if no consumer setup

    # # SINK
    #
    # async def __call__(self, message) -> None:
    #
    #     # structure of a message on a private channel:
    #     # - https://docs.kraken.com/websockets-beta/#message-ownTrades
    #     # - https://docs.kraken.com/websockets-beta/#message-openOrders
    #     data = message[0]
    #     channel = message[1]
    #
    #     if channel == self.channel_name:
    #         # also calling the parsed model to store the pair here as well...
    #         parsed = self.schema.load(data, many=isinstance(data, list))
    #         await self.queue.put(parsed)
    #     # otherwise nothing happens
    #
    # ## SOURCE
    #
    # async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
    #     while self.queue:
    #         yield await self.queue.get()
    #         self.queue.task_done()


_ticker_schema = TickerWSSchema()
_ohlcupdate_schema = OHLCUpdateSchema()
_trade_schema = TradeWSSchema()
_owntrades_schema = ownTradeWSSchema()


def channel(name: str, pair = None, id = None):
    """ Create channel instances to manage streams of data from a kraken publisher.
    """
    if name == "ticker":
        chan = PublicChannel(pair=pair,
                             id=id,
                             channel_name=name,
                             schema=_ticker_schema)

    elif name.startswith("ohlc"):  # name depends also on interval !
        chan = PublicChannel(pair=pair,
                             id=id,
                             channel_name=name,
                             schema=_ohlcupdate_schema)

    elif name.startswith("trade"):
        chan = PublicChannel(pair=pair,
                             id=id,
                             channel_name=name,
                             schema=_trade_schema)

    elif name.startswith("ownTrades"):
        chan = PrivateChannel(channel_name=name,
                              schema=_owntrades_schema)
    else:
        raise NotImplementedError(f"Unknown channel name '{name}'. please add it to the code...")

    return chan


if __name__ == '__main__':
    raise NotImplementedError