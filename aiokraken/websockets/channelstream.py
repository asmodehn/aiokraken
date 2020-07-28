import asyncio
import typing

from aiokraken.rest import AssetPairs

from aiokraken.websockets.channelsubscribe import ChannelPrivate, PublicChannelSet


class SubStreamPrivate:
    # note pair matching is done inside the parser itself
    # here we rely solely on id
    channel: ChannelPrivate
    queue: asyncio.Queue = None

    def __init__(self, *, channelprivate: ChannelPrivate):

        self.channel = channelprivate
        self.queue = asyncio.Queue(maxsize=8)  # to quickly trigger exception if no consumer setup.

    def __await__(self):
        # we wait on future
        async def waitfut():
            await self.channel.subid
            return self
        return waitfut().__await__()

    # SINK

    async def __call__(self, *, data: typing.Any, channel: str) -> None:
        # channel name and pair matching has been done before. here we only need the channel_id.
        # parsing message ignoring errors
        if parsed := self.channel(data=data):
            await self.queue.put(parsed.value)
        else:
            print(parsed.value)  # output directly the error # TODO : proper log...

    ## SOURCE

    async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
        while self.queue and self.channel.subid is not None:  # channel.subid is used to detect when we unsubscribe
            yield await self.queue.get()
            self.queue.task_done()


class SubStream:
    # note pair matching is done inside the parser itself
    # here we rely solely on id
    pairs: AssetPairs
    channels: PublicChannelSet
    queue: asyncio.Queue = None

    def __init__(self, *, channelset: PublicChannelSet, pairs: AssetPairs):
        self.pairs = pairs
        self.channels = channelset
        self.queue = asyncio.Queue(maxsize=8)  # to quickly trigger exception if no consumer setup.

    def __await__(self):

        async def sync():
            for f in [f for p, f in self.channels.subids.items() if p in self.pairs.values()]:
                await f
            return self

        return sync().__await__()

    # SINK

    def __contains__(self, item: int):
        return item in self.channels

    async def __call__(self, *, chan_id: int, data: typing.Any, channel: str, pair: str) -> None:
        # channel name and pair matching has been done before. here we only need the channel_id.
        # parsing message ignoring errors
        if pair in self.pairs:  # we need to parse only pairs we are interested in !
            if parsed := self.channels(chan_id=chan_id, data=data, pair=pair):
                await self.queue.put(parsed.value)
            else:
                print(parsed.value)  # output directly the error # TODO : proper log...

    ## SOURCE

    async def __aiter__(self):  # hints: -> typing.AsyncGenerator[yield, send, return] ????
        while self.queue and self.channels.subids:  # channel.subid is used to detect when we unsubscribe
            yield await self.queue.get()
            self.queue.task_done()

