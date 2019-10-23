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


class Currency(Enum):
    def __str__(self) -> str:
        return f'{self.name}'

    def __repr__(self) -> str:
        return f'{self.name}'


# Enums to store accepted currencies.
# Unknown currencies will be ignored
class Fiat(Currency):
    """
    >>> Fiat('EUR')
    EUR
    """
    EUR= 'EUR'
    USD= 'USD'
    CAD= 'CAD'
    KRW= 'KRW'
    JPY= 'JPY'


class Crypto(Currency):
    """
    >>> Crypto('BTC')
    BTC
    """
    BTC= 'BTC'
    ETH= 'ETH'


class Alt(Currency):
    """
    >>> Alt("XRP")
    XRP
    """
    XRP= 'XRP'


def currency(c: str) -> typing.Optional[Currency]:
    """
    >>> c = currency('EUR')
    >>> type(c)
    <enum 'Fiat'>
    >>> c
    EUR

    >>> c = currency('BTC')
    >>> type(c)
    <enum 'Crypto'>
    >>> c
    BTC

    >>> c = currency('XRP')
    >>> type(c)
    <enum 'Alt'>
    >>> c
    XRP

    """
    if c in Fiat.__members__:
        return getattr(Fiat, c)
    elif c in Crypto.__members__:
        return getattr(Crypto, c)
    elif c in Alt.__members__:
        return getattr(Alt, c)
    else:
        raise CurrencyError


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])

