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
class KCurrency(Enum):
    """
    >>> KCurrency('EUR')
    EUR
    >>> KCurrency('XBT')
    BTC
    >>> KCurrency.XBT == KCurrency.BTC
    True
    >>> str(KCurrency('XBT'))
    'XBT'
    """
    # Fiat
    EUR = 'EUR'
    USD = 'USD'
    CAD = 'CAD'
    KRW = 'KRW'
    JPY = 'JPY'
    # Crypto (aliases allowed)
    BTC = 'XBT'
    XBT = 'XBT'
    ETC = 'ETC'
    ETH = 'ETC'
    XRP = 'XRP'

    def __str__(self) -> str:
        """Kraken representation"""
        return f'{self.value}'

    def __repr__(self) -> str:
        """Internal representation"""
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
        return KCurrency(value)

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        return value.value


@st.composite
def KCurrencyStringStrategy(draw):
    model = draw(KCurrencyStrategy())
    field = KCurrencyField()
    return field.serialize('a', {'a': model})


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])

