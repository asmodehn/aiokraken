# TODO : test channel.
# Design : channel.py should be functional, easily testable (ref : "sans-io" https://sans-io.readthedocs.io/)
import unittest

from aiokraken.websockets.schemas.ticker import TickerWSSchema, TickerWS
from hypothesis import given
from hypothesis.strategies import data

from aiokraken.websockets.tests.strats.st_channel import st_channel


class TestChannel(unittest.TestCase):

    @given(channel=st_channel(), data=data())
    def test_valid(self, channel, data):
        # verifying channel is actually what we expect
        assert len(channel.channel_name) > 0
        assert channel.channel_id > 0
        assert channel.schema is not None
        assert len(channel.callbacks) == 0  # callbacks empty when channel is created

        # # drawing data in test to allow schema parsing
        # data(channel.schema.strategy)
        # # TODO : test !
        # channel()

    @given(channel=st_channel(), data=data())
    def test_samplecallback(self, channel, data):

        # hardcoding schema for now
        channel.schema = TickerWSSchema()

        received = None
        def cbtest(msg):
            nonlocal received
            received = msg

        channel.callbacks.append(cbtest)

        # generating message data
        tick_msg = data.draw(TickerWSSchema.strategy())
        channel(tick_msg)

        # make sure the message was relayed to the callback
        assert isinstance(received, TickerWS) and received == TickerWSSchema().load(tick_msg)
