from __future__ import annotations

# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc
import asyncio
from dataclasses import dataclass, field

import typing

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.subscribe import Subscribe

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema


@dataclass(frozen=True)
class Channel:
    """
    A channel, calls its callback when a message is received.

    IMPORTANT : the same message CAN be received multiple times for various reason.
    Unicity of the message semantics is up to the message data structure itself

    """
    channel_id: int
    channel_name: str
    pair: str   # Important : given kraken WS API design, it seems we have one pair per channel
                # BUT one can subscribe to multiple pairs at once...

    schema: BaseSchema


if __name__ == '__main__':
    raise NotImplementedError