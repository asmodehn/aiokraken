import functools
import unittest
from ..limiter import limiter


class TestLimiterSync(unittest.TestCase):

    def sleeper(self, delay):
        self.slept = delay

    def timer(self, incr=0):
        return self.clock

    def limited(self):
        self.limited_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        # We build a limiter based on a local test clock
        self.limiter = functools.partial(limiter, timer=self.timer, sleeper= self.sleeper)

        self.limited_call = False

    def test_nonskippable(self):
        assert self.limited_call is False
        # setting up limiter
        limited = self.limiter(period=5, skippable=False)(self.limited)

        # First call should pass, with minimum sleeping
        r = limited()
        assert self.limited_call is True
        assert self.slept == 6  # + epsilon !
        assert r == self.result

        # reset
        self.limited_call = False
        self.result = 51

        # move clock forward but not enough
        self.clock = 3
        self.slept = 0  # and reset slept

        # Second fast call should call sleep for the period missing
        rb = limited()
        assert self.slept == 3  # dont forget the epsilon !
        assert self.limited_call is True
        # return should be the cached result (since we didnt call it).
        # Note this is not a valid usecase in practice when sleep is actually sleeping
        assert rb == self.result

        # Later call should not call sleep at all
        self.result = 73

        # move clock forward more than enough
        self.clock = 3 + 6
        self.slept = 0  # and reset slept

        # Third call should not call sleep
        rt = limited()
        assert self.slept == 0
        assert self.limited_call is True
        assert rt == self.result

    def test_skippable(self):
        assert self.limited_call is False
        # setting up limiter
        limited = self.limiter(period=5, skippable=True)(self.limited)

        # First call should pass, with minimum sleeping
        r = limited()
        assert self.limited_call is True
        assert self.slept == 6
        assert r == self.result

        # reset
        self.limited_call = False
        self.result = 51
        # move clock forward but not enough
        self.clock = 3
        self.slept = 0  # and reset slept

        # Second call should not block by calling sleep, but skip
        rb = limited()
        assert self.limited_call is False
        assert self.slept == 0
        # return should be the cached result (since we didnt call it).
        # Note this is not a valid usecase in practice when sleep is actually sleeping
        assert rb == r

        # Later call should not call sleep at all
        self.result = 73

        # move clock forward more than enough
        self.clock = 3 + 6
        self.slept = 0  # and reset slept

        # Third call should not call sleep
        rt = limited()
        assert self.slept == 0
        assert self.limited_call is True
        assert rt == self.result



# class TestLimiterASync(unittest.TestCase):
#     raise NotImplementedError  # TODO HOWTO ???
# Ref : see https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code


if __name__ == '__main__':
    unittest.main()
