import asyncio
import unittest
from random import randint

from aiokraken.rest.tests.strats.st_assetpairs import st_assetpairs

from aiokraken.websockets.schemas.subscribe import Subscription

from aiokraken.model.tests.strats.st_assetpair import AssetPairStrategy
from hypothesis import given
from hypothesis import strategies as st

import aiokraken.websockets.channelsubscribe
from aiokraken.websockets.channelsubscribe import (
    PublicChannelSet, private_subscribe, private_subscribed, ChannelPrivate,
    private_unsubscribe, public_subscribe, public_subscribed, public_unsubscribe
)

# TODO: CAREFUL there are tricky, yet untested, concurrency pain points here... we might need some async.Locks...


class TestChannelPrivate(unittest.TestCase):

    @given(channel_name=st.sampled_from(["ownTrades", "openOrders"]))
    def test_subscribe_flow(self, channel_name):

        async def runner():
            chan = ChannelPrivate(loop=asyncio.get_running_loop())

            assert isinstance(chan.subid, asyncio.Future)
            assert not chan.subid.done()
            assert chan.parser is None

            chan.subscribed(channel_name=channel_name)

            assert chan.subid.done()
            assert callable(chan.parser)

        asyncio.run(runner())


class TestPublicChannelSet(unittest.TestCase):

    @given(channel_name=st.sampled_from(["trade", "ticker"]),  # TODO : ohlc
           pairs=st_assetpairs())
    def test_subscribe_flow(self, channel_name, pairs):
        async def runner():
            chan = PublicChannelSet()

            chan.subscribe(pairs=pairs, loop=asyncio.get_running_loop())

            for p in pairs.values():
                assert isinstance(chan[p], asyncio.Future) and not chan[p].done()
                assert not chan.parsers  # should be empty here !

            for p in pairs.values():  # TODO : shuffle ?
                cid = randint(0,9999)
                chan.subscribed(pairstr=p.wsname, channel_name=channel_name, channel_id=cid)
                assert chan[p].done() and chan[p].result() == cid
                assert callable(chan[cid])  # parser available

            chan.unsubscribe(pairs=pairs)

            for p in pairs.values():
                assert p not in chan.subids  # channel ids are gone !
                assert chan  # keeping parsers around in case of late incoming message
                # TODO : unsubscribe flow


# class TestPublicChannelSubscribe(unittest.IsolatedAsyncioTestCase):
class TestPublicChannelSubscribe(unittest.TestCase):

    @given(pairs=st_assetpairs())
    # async def test_trade_subscribe_flow(self, pairs):
    def test_trade_subscribe_flow(self, pairs):
        async def runner():
            # Happy path
            subscribe, chan1 = public_subscribe(pairs=pairs, subscription=Subscription(name="trade"),
                                                loop=asyncio.get_running_loop())
            assert isinstance(chan1, PublicChannelSet)
            for p in pairs.values():
                assert p.wsname in subscribe.pair
                assert isinstance(chan1[p], asyncio.Future)
                assert not chan1[p].done()

            for p in pairs.values():
                chan2 = public_subscribed(channel_name="trade", pairstr=p.wsname, channel_id=randint(0, 9999))
                assert chan2 == chan1  # should be the exact same thing
                assert chan2[p].done()
                cid = chan2[p].result()
                assert cid in chan2 and callable(chan2[cid])

            for p in pairs.values():
                assert isinstance(chan1[p], asyncio.Future)
                assert chan1[p].done()

            unsubscribe, chan3 = public_unsubscribe(pairs=pairs, subscription=Subscription(name="trade"))
            for p in pairs.values():
                assert p.wsname in unsubscribe.pair
                assert not p in chan3

        asyncio.run(runner())

    @given(pairs=st_assetpairs())
    def test_ticker_subscribe_flow(self, pairs):

        async def runner():
            # Happy path # TODO : test various sequences
            subscribe, chan1 = public_subscribe(pairs=pairs, subscription=Subscription(name="ticker"),
                                                loop=asyncio.get_running_loop())
            assert isinstance(chan1, PublicChannelSet)
            for p in pairs.values():
                assert isinstance(chan1[p], asyncio.Future)
                if p.wsname in subscribe.pair:  # we need to subscribe to it
                    assert not chan1[p].done()
                else:
                    assert chan1[p].done()  # already subscribed to it

            for p in pairs.values():
                cid = randint(0, 9999)
                chan2 = public_subscribed(channel_name="ticker", pairstr=p.wsname, channel_id=cid)
                assert chan2 == chan1  # should be the exact same thing
                assert chan2[p].done()  # this pair is subscribed to
                assert cid == chan2[p].result()  # we have the cid
                assert cid in chan2 and callable(chan2[cid])  # we can access the parser

            unsubscribe, chan3 = public_unsubscribe(pairs=pairs, subscription=Subscription(name="ticker"))
            assert chan3 == chan1  # still the same thing
            for p in pairs.values():
                assert not p in chan3
                if p.wsname in unsubscribe.pair:
                    assert p not in chan3
                assert p.wsname in unsubscribe.pair

        asyncio.run(runner())

    async def test_ohlc_subscribe_flow(self, pairs, interval):
        raise NotImplementedError


class TestPrivateChannelSubscribe(unittest.IsolatedAsyncioTestCase):

    async def test_ownTrades_subscribe_flow(self):
        # The happy path...
        chan1 = private_subscribe("ownTrades", loop=asyncio.get_running_loop())
        assert isinstance(chan1, ChannelPrivate)
        assert isinstance(chan1.subid, asyncio.Future)

        chan2 = private_subscribed("ownTrades")
        assert chan2 == chan1  # should be the exact same thing
        assert chan2.subid == chan1.subid
        assert chan1.subid.done()
        assert chan2.subid.done()

        private_unsubscribe("ownTrades")
        # Note these exists (copies), but just became useless "proxies"
        assert chan1
        assert chan2
        assert aiokraken.websockets.channelsubscribe.ownTrades is None

    async def test_openOrders_subscribe_flow(self):
        # The happy path...
        chan1 = private_subscribe("openOrders", loop=asyncio.get_running_loop())
        assert isinstance(chan1, ChannelPrivate)
        assert isinstance(chan1.subid, asyncio.Future)

        chan2 = private_subscribed("openOrders")
        assert chan2 == chan1  # should be the exact same thing
        assert chan2.subid == chan1.subid
        assert chan1.subid.done()
        assert chan2.subid.done()

        private_unsubscribe("openOrders")
        # Note these exists (copies), but just became useless "proxies"
        assert chan1
        assert chan2
        assert aiokraken.websockets.channelsubscribe.openOrders is None


if __name__ == '__main__':
    unittest.main()
