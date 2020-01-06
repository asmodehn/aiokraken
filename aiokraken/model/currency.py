#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import typing
from enum import Enum

from dataclasses import dataclass

from ..rest.exceptions import AIOKrakenException


class CurrencyError(AIOKrakenException):
    pass


class SymbolError(AIOKrakenException):
    pass


"""
Module defining Currency and Symbol
To use types to filter out what we are not interested in.
"""


# Enum to store accepted currencies.
# Unknown currencies will be ignored
# Ref : https://support.kraken.com/hc/en-us/articles/360000678446
# Ref : https://support.kraken.com/hc/en-us/articles/360001185506
class KCurrency(Enum):
    """
    >>> KCurrency('EUR')
    EUR

    >>> KCurrency('XBT')
    XBT

    Careful, aliases are not handled when parsing
    >>> KCurrency('BTC')
    Traceback (most recent call last):
        ...
    ValueError: 'BTC' is not a valid KCurrency

    However:
    >>> KCurrency.BTC
    XBT

    Similarly:
    >>> KCurrency('XXBT')
    Traceback (most recent call last):
        ...
    ValueError: 'XXBT' is not a valid KCurrency

    >>> KCurrency.XBT == KCurrency.BTC
    True

    str() returns the value for serializing
    >>> str(KCurrency.BTC)
    'XBT'

    repr() returns the (first in the list) name for internal usage
    >>> repr(KCurrency.BTC)
    'XBT'

    """
    # Fiat
    EUR = 'EUR'
    USD = 'USD'
    CAD = 'CAD'
    KRW = 'KRW'
    JPY = 'JPY'
    # Crypto (name aliases allowed. value must be unique, as per the desired semantic)
    # Maybe ? https://www.notinventedhere.org/articles/python/how-to-use-strings-as-name-aliases-in-python-enums.html
    XBT = 'XBT'
    BTC = 'XBT'
    ETC = 'ETC'
    ETH = 'ETH'
    XRP = 'XRP'
    EOS = 'EOS'
    BCH = 'BCH'
    ADA = 'ADA'
    XTZ = 'XTZ'
    BSV = 'BSV'

    def __str__(self) -> str:
        """Kraken default representation for sending data."""
        return f'{self.value}'

    def __repr__(self) -> str:
        """Internal representation, unique."""
        return f'{self.name}'


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])

