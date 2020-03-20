import unittest

from aiokraken.websockets.schemas.subscribe import Subscription, Subscribe
from hypothesis import given
import hypothesis.strategies as st
from aiokraken.websockets.schemas.tests.strats.st_subscribe import st_subscription, st_subscribe


class TestSubscription(unittest.TestCase):

    @given(sub = st_subscription())
    def test_valid_strategy(self, sub):
        assert isinstance(sub, Subscription)

        # TODO : replace this with proper mypy typechecks checks + refine
        assert isinstance(sub.name, str)
        assert isinstance(sub.interval, int)
        assert isinstance(sub.depth, int)
        assert isinstance(sub.token, str)


class TestSubscribe(unittest.TestCase):

    @given(sub= st_subscribe())
    def test_valid_strategy(self, sub):
        assert isinstance(sub, Subscribe)

        # TODO : replace this with proper mypy typechecks checks + refine
        assert isinstance(sub.pair, list)
        assert sub.reqid is None or isinstance(sub.reqid, int)
        assert isinstance(sub.subscription, Subscription)


if __name__ == '__main__':
    unittest.main()
