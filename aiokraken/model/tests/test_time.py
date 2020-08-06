import contextlib
import locale
import unittest

from datetime import timezone
from aiokraken.model.time import Time

from aiokraken.model.tests.strats.st_time import st_time
from hypothesis import given, settings, Verbosity, HealthCheck
from hypothesis.strategies import sampled_from


class TestTime(unittest.TestCase):

    @contextlib.contextmanager
    def localectx(self, lcl_string:str):
        #  If alternate locale is not available, the test will be
        # skipped, please install this locale for it to run
        currentLocale = locale.getlocale()
        try:
            try:
                locale.setlocale(locale.LC_ALL, lcl_string)
            except locale.Error:
                self.skipTest(f"The {lcl_string} locale is not installed.")

            # provide context with locale set
            yield locale.getlocale(locale.LC_ALL)

        finally:
            # reset the original locale (finally guarantees it)
            locale.setlocale(locale.LC_ALL, currentLocale)

    @given(t=st_time())
    def test_unixtime(self, t: Time):
        # make sure we are storing a timestamp internally,
        # that is accessible (to interface with kraken on with the same semantics)
        assert t.unixtime == t.timestamp()

    @given(t=st_time())
    def test_timezone(self, t: Time):
        # TODO : refine this (what if not utc ??)
        assert t.timezone == timezone.utc

    @given(t=st_time())
    def test_repr_en_us_utf8(self, t:Time):

        with self.localectx("en_US.UTF-8") as lcl:
            assert lcl == ("en_US","UTF-8")  # to be sure context is set

            r = repr(t)

            # Ref : https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
            format_str = "%Y-%m-%dT%H:%M:%S.%f+00:00" if t.microsecond else "%Y-%m-%dT%H:%M:%S+00:00"
            assert r == t.strftime(format_str), r +'!=' + t.strftime(format_str)  # UTC hardcoded

    @given(t=st_time())
    def test_repr_fr_fr_utf8(self, t: Time):

        with self.localectx("fr_FR.UTF-8") as lcl:
            assert lcl == ("fr_FR","UTF-8")  # to be sure context is set

            r = repr(t)

            # Ref : https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior
            format_str = "%Y-%m-%dT%H:%M:%S.%f+00:00" if t.microsecond else "%Y-%m-%dT%H:%M:%S+00:00"
            assert r == t.strftime(format_str), r + '!=' + t.strftime(format_str)  # UTC hardcoded

    @given(t=st_time())
    def test_str_en_us_utf8(self, t:Time):

        with self.localectx("en_US.UTF-8") as lcl:
            assert lcl == ("en_US","UTF-8")  # to be sure context is set

            s = str(t)

            format_str = "%c %Z"  # this depends on locale set !
            assert s == t.strftime(format_str), s + "!=" + t.strftime(format_str)  # UTC hardcoded

    @given(t=st_time())
    def test_str_fr_fr_utf8(self, t:Time):

        with self.localectx("fr_FR.UTF-8") as lcl:
            assert lcl == ("fr_FR","UTF-8")  # to be sure context is set

            s = str(t)

            format_str = "%c %Z"  # this depends on locale set !
            assert s == t.strftime(format_str), s + "!=" + t.strftime(format_str)  # UTC hardcoded


if __name__ == "__main__":
    unittest.main()
