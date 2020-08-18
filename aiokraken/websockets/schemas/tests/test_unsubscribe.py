import unittest

from aiokraken.websockets.schemas.unsubscribe import Unsubscribe, ChannelUnsubscribe

from aiokraken.websockets.schemas.subscribe import Subscription, Subscribe
from hypothesis import given
import hypothesis.strategies as st
from aiokraken.websockets.schemas.tests.strats.st_unsubscribe import st_unsubscribe, st_channel_unsubscribe


class TestUnsubscribe(unittest.TestCase):

    @given(sub= st_unsubscribe())
    def test_valid_strategy(self, sub):
        assert isinstance(sub, Unsubscribe)

        # TODO : replace this with proper mypy typechecks checks + refine
        assert isinstance(sub.pair, list)
        assert sub.reqid is None or isinstance(sub.reqid, int)
        assert isinstance(sub.subscription, Subscription)


class TestChannelUnsubscribe(unittest.TestCase):

    @given(sub= st_channel_unsubscribe())
    def test_valid_strategy(self, sub):
        assert isinstance(sub, ChannelUnsubscribe)

        # TODO : replace this with proper mypy typechecks checks + refine
        assert sub.reqid is None or isinstance(sub.reqid, int)
        assert isinstance(sub.channel_id, int)


if __name__ == '__main__':
    unittest.main()
