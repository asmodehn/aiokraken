from datetime import datetime, timezone
import time

# https://wiki.python.org/moin/WorkingWithTime
from dataclasses import dataclass


@dataclass(frozen=True)
class Time:
    """
    A cross exchange python representation of time.
    Includes domain specific semantic about correctness of data.

    TODO : Uses rfc 3339 rfc 1123  iso8601 ???
    """

    unixtime: int  # time stamp, number of secs since epoch (ie unix time)
    timezone: timezone = timezone.utc

    def __post_init__(self):
        # TODO : currently assumed perfect  (0)
        object.__setattr__(self, 'clockskew', 0)  # careful to not include timezone here

    # TODO : make sure we have proper time sync with server (and with pandas datetime methods...)
    # REf : https://stackoverflow.com/questions/10256093/how-to-convert-ctime-to-datetime-in-python

    def __repr__(self):
        """ non ambiguous representation"""
        return self.isoformat()

    def __str__(self):
        """ human-centric representation (careful with locale... and timezone)"""
        return self.strftime("%c %Z")

    def __getattr__(self, item):
        """ delegating to a datetime instance"""
        return getattr(datetime.fromtimestamp(self.unixtime, tz=self.timezone), item)

