from __future__ import annotations

# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc
import asyncio
from dataclasses import dataclass, field

import typing

from aiokraken.websockets.schemas.openorders import openOrderWSSchema

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


_ticker_schema = TickerWSSchema()
_ohlcupdate_schema = OHLCUpdateSchema()
_trade_schema = TradeWSSchema()
_owntrades_schema = ownTradeWSSchema()
_openorders_schema = openOrderWSSchema()


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

    elif name.startswith("openOrders"):
        chan = PrivateChannel(channel_name=name,
                              schema = _openorders_schema)

    else:
        raise NotImplementedError(f"Unknown channel name '{name}'. please add it to the code...")

    return chan


if __name__ == '__main__':
    raise NotImplementedError