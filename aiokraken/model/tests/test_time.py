import unittest

from datetime import timezone
from aiokraken.model.time import Time

from aiokraken.model.tests.strats.st_time import st_time
from hypothesis import given, settings, Verbosity, HealthCheck
from hypothesis.strategies import sampled_from


class TestTime(unittest.TestCase):

    @given(t=st_time())
    def test_unixtime(self, t: Time):
        # make sure we are storing a timestamp internally,
        # that is accessible (to interface with kraken on with the same semantics)
        assert t.unixtime == int(t.timestamp())

    @given(t=st_time())
    def test_timezone(self, t: Time):
        # TODO : refine this (what if not utc ??)
        assert t.timezone == timezone.utc

    @given(t=st_time())
    def test_repr(self, t:Time):
        r = repr(t)
        # Ref : https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
        format_str = "%Y-%b-%dT%H:%M:%S+00:00"
        assert r == t.strftime(format_str), r +'!=' + t.strftime(format_str)  # UTC hardcoded

    @given(t=st_time())
    def test_str(self, t:Time):
        s = str(t)
        format_str = "%a %b %d %H:%M:%S %Y UTC"
        assert s == t.strftime(format_str), s + "!=" + t.strftime(format_str)  # UTC hardcoded


if __name__ == "__main__":
    unittest.main()
