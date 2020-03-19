
# This concept of channels comes directly from the Kraken API docs : https://docs.kraken.com/websockets/#message-ohlc

# <class 'dict'>: {'connectionID': 12997236506998204415, 'event': 'systemStatus', 'status': 'online', 'version': '1.0.0'}


from dataclasses import dataclass, field

import typing


from aiokraken.rest.schemas.base import BaseSchema


@dataclass()
class Channel:
    channel_id: int
    channel_name: str
    pair: str

    schema: BaseSchema
    callbacks: list = field(default_factory=list)

    def __call__(self, data):
        try:
            parsed = self.schema.load(data)
            # calling callbacks one after the other, sync.
            for c in self.callbacks:
                c(parsed)
            # handling the return is up to the user
        except Exception as e:
            raise