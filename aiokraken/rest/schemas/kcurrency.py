#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import functools
import random
import typing
from enum import Enum

from dataclasses import dataclass

from marshmallow import fields
from hypothesis import strategies as st

from aiokraken.model.tests.test_currency import KCurrencyStrategy

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

from ...model.currency import KCurrency


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
        'CAD': ['CAD', 'ZCAD'],
        'JPY': ['JPY', 'ZJPY'],
        'KRW': ['KRW', 'ZKRW'],
        # Crypto
        'XBT': ['XBT', 'BTC', 'XXBT'],
        'BSV': ['BSV', 'XBSV'],
        'BCH': ['BCH', 'XBCH'],
        'ETH': ['ETH', 'XETH'],
        'ETC': ['ETC', 'XETC'],
        'EOS': ['EOS', 'XEOS'],
        'XRP': ['XRP', 'XXRP'],
        'XTZ': ['XTZ', 'XXTZ'],
        'ADA': ['ADA', 'XADA'],

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


@st.composite
def KCurrencyStringAliasStrategy(draw):
    model = draw(KCurrencyStrategy())
    field = KCurrencyField()
    # returns a random alias...
    assert model.value in field._alias_map, f"{model.value} not in {field._alias_map} !"
    aliases = field._alias_map.get(model.value)
    return aliases[random.randint(0, len(aliases)-1)]


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])

