# TODO : test channel.
# Design : channel.py should be functional, easily testable (ref : "sans-io" https://sans-io.readthedocs.io/)
import unittest

from aiokraken.websockets.schemas.trade import TradeWS

from aiokraken.websockets.schemas.ohlc import OHLCUpdate

from aiokraken.websockets.schemas.ticker import TickerWSSchema, TickerWS
from hypothesis import given, settings, Verbosity
from hypothesis.strategies import data

from aiokraken.websockets.tests.strats.st_channel import (
    st_public_channel, st_private_channel
)


class TestPrivateChannels(unittest.TestCase):

    @settings(verbosity=Verbosity.verbose)
    @given(channel=st_private_channel(), data=data())
    def test_init_call(self, channel, data):
        # verifying channel is actually what we expect
        assert len(channel.channel_name) > 0
        assert channel.schema is not None

        # drawing data in test to allow schema parsing
        message = data(channel.schema.strategy())
        parsed = channel(message)

        assert isinstance(parsed, (TickerWS, TradeWS, OHLCUpdate))




# class TestPublicChannels(unittest.TestCase):
#     raise NotImplementedError


if __name__ == '__main__':
    unittest.main()
