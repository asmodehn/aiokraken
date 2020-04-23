
# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc


from dataclasses import dataclass, field

import typing

from aiokraken.websockets.schemas.subscribe import Subscribe

from aiokraken.rest.exceptions import AIOKrakenSchemaValidationException

from aiokraken.rest.schemas.base import BaseSchema


@dataclass()
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

    # We store a reference to the request that created this channel (for potential reuse)
    subscribe_request: Subscribe = field(repr=False)

    schema: BaseSchema
    callbacks: list = field(default_factory=list)

    def __call__(self, data):
        try:
            parsed = self.schema.load(data)
        except AIOKrakenSchemaValidationException as aiosve:
            if isinstance(data, list) and len(data) == len(self.schema.declared_fields):
                data_dict = dict()
                # attempt again by iterating on fields
                for f, d in zip(self.schema.declared_fields.keys(), data):
                    data_dict[f] = d
                parsed = self.schema.load(data_dict)
            else:
                raise

        # calling callbacks one after the other, sync.
        for c in self.callbacks:
            c(parsed)
            # handling the return is up to the user