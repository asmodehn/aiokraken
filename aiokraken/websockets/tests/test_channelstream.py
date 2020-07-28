import asyncio
import unittest
from random import randint

from aiokraken.rest.assetpairs import AssetPairs
from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy

from aiokraken.model.assetpair import AssetPair

from aiokraken.websockets.schemas.trade import TradeWSSchema
from hypothesis import given

from aiokraken.websockets.channelstream import SubStream, SubStreamPrivate

from aiokraken.websockets.channelsubscribe import ChannelPrivate, PublicChannelSet

from aiokraken.websockets.channelparser import ownTradeWSSchema


class TestSubStreamPrivate(unittest.TestCase):

    @given(data=ownTradeWSSchema.strategy())
    def test_ownTrades_await_call_aiter(self, data):

        chan = ChannelPrivate()
        schm = ownTradeWSSchema()

        async def runner():

            # TODO : a controlled way to test all possible sequences here...

            chan.subscribe(loop=asyncio.get_running_loop()),
            chan.subscribed(channel_name="ownTrades")

            stream = SubStreamPrivate(channelprivate=chan)
            assert stream == await stream  # waiting for subscribed() called

            await stream(data=data, channel="ownTrades")
            assert stream.queue.qsize() == 1

            chan.unsubscribe()

            async for msg in stream:
                assert msg == schm.load(data=data)

        asyncio.run(runner())

    # TODO : openOrders is the same...

    @given(data=TradeWSSchema.strategy(), pair=AssetPairStrategy())
    def test_Trade_await_call_aiter(self, data, pair):

        chan = PublicChannelSet()
        schm = TradeWSSchema()

        async def runner():
            pairs = AssetPairs(assetpairs_as_dict={pair.wsname: pair})

            # TODO : a controlled way to test all possible sequences here...

            chan.subscribe(pairs=pairs, loop=asyncio.get_running_loop()),
            cid = randint(0, 9999)
            chan.subscribed(channel_name="trade", pairstr=pair.wsname, channel_id=cid)

            stream = SubStream(channelset=chan, pairs=pairs)
            assert stream == await stream  # waiting for subscribed() called

            rawdata = [v for v in data.values()]  # TODO : post dump ??
            await stream(chan_id=cid, data=rawdata, channel="trade", pair=pair.wsname)
            assert stream.queue.qsize() == 1

            chan.unsubscribe(pairs=pairs)

            async for msg in stream:
                assert msg == schm.load(data=data)

        asyncio.run(runner())


if __name__ == '__main__':
    unittest.main()
