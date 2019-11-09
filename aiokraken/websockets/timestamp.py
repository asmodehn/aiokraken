from __future__ import annotations

import functools
from datetime import timezone, datetime

from dataclasses import dataclass, field

""" Module to handle everything related to time conversion and manipulation"""

# TODO : define Timestamp as float/decimal type, to avoid yet another class level ??


@dataclass(frozen=True)
class Timestamp:
    """
    Gives a timestamp of NOW!
    >>> Timestamp()  # doctest: +ELLIPSIS
    Timestamp(stamp=...)

    The now class method can also be patched:
    >>> def now():
    ...     print("NOW!")
    >>> Timestamp.now = now
    >>> Timestamp()
    NOW!
    Timestamp(stamp=None)
    """
    @staticmethod
    def now() -> float:
        return datetime.now().replace(tzinfo=timezone.utc).timestamp()

    stamp: float = field(default=None, init=False)

    def __post_init__(self):
        object.__setattr__(self, "stamp", Timestamp.now())

    # TODO : convert stamp to decimal in a way that makes sense, given the precision of the machine...


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
