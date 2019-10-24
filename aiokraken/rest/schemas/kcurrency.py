#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
import typing
from enum import Enum

from dataclasses import dataclass

from marshmallow import fields
from hypothesis import strategies as st

if not __package__:
    __package__ = 'aiokraken.rest.schemas'

from ..exceptions import AIOKrakenException


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


# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
KCurrencyStrategy = functools.partial(st.sampled_from, KCurrency)


class KCurrencyField(fields.Field):
    """
    A field to interface with marshmallow

    >>> KCurrencyField().serialize('EUR', obj=KCurrency('EUR'))
    'EUR'
    >>> KCurrencyField().deserialize('EUR')
    EUR
    """

    _alias_map = {
        # Fiat
        'EUR': ['EUR', 'ZEUR'],
        'GBP': ['GBP', 'ZGBP'],
        'USD': ['USD', 'ZUSD'],
        # Crypto
        'XBT': ['XBT', 'BTC', 'XXBT'],
        'ETH': ['ETH', 'XETH'],
        'ETC': ['ETC', 'XETC'],
        'XRP': ['XRP', 'XXRP'],

    }

    def _deserialize(
            self,
            value: typing.Any,
            attr: typing.Optional[str],
            data: typing.Optional[typing.Mapping[str, typing.Any]],
            **kwargs
    ):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :param value: The value to be deserialized.
        :param attr: The attribute/key in `data` to be deserialized.
        :param data: The raw input data passed to the `Schema.load`.
        :param kwargs: Field-specific keyword arguments.
        :raise ValidationError: In case of formatting or validation failure.
        :return: The deserialized value.
        """

        c = None
        try:
            c = KCurrency(value)
        except ValueError as ve:
            # value not using recognisable name. maybe alias ?
            for k, v in self._alias_map.items():
                if value in v:
                    c = KCurrency(k)

        if c is None:
            raise ValueError(f"'{value}' is not a valid KCurrency, nor a known alias")
        else:
            return c

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        # serializing with default data
        return value.value


@st.composite
def KCurrencyStringStrategy(draw):
    model = draw(KCurrencyStrategy())
    field = KCurrencyField()
    return field.serialize('a', {'a': model})


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])

