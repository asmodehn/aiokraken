import random

import marshmallow
import typing
from dataclasses import dataclass

from marshmallow import fields, pre_load, post_load

from aiokraken.model.pair import PairModel
from aiokraken.model.tests.strats.st_pair import PairStrategy

if not __package__:
    __package__ = 'aiokraken.rest.schemas'

from .base import BaseSchema
from ..exceptions import AIOKrakenException
from ...model.tests.strats.st_currency import KCurrency, KCurrencyStrategy
from .kcurrency import KCurrencyField
from hypothesis import given, strategies as st


class PairField(fields.Field):
    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]],
        **kwargs,
    ):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :param value: The value to be deserialized.
        :param attr: The attribute/key in `data` to be deserialized.
        :param data: The raw input data passed to the `Schema.load`.
        :param kwargs: Field-specific keyword arguments.
        :raise ValidationError: In case of formatting or validation failure.
        :return: The deserialized value.

        """
        p = {}
        i = 1
        iv = value[:]  # we need to keep value intact while parsing
        for k in ["base", "quote"]:
            while i <= len(iv):
                # some kind of pattern matching... for python 3.7
                # TODO : is there a better way ? Overload enum ? try/except ?
                # Ref : https://pypi.org/project/algebraic-data-types/
                # Ref : https://github.com/python/mypy/issues/2464

                try:
                    p.setdefault(k, KCurrencyField().deserialize(iv[:i]))
                    iv = iv[i:]
                    i = 1
                    break
                except ValueError as ve:
                    # not a valid currency expected
                    i += 1

        try:
            pm = PairModel(base=p["base"], quote=p["quote"])
        except KeyError as ke:
            # reinterpreting the exception (is there a better way ?)
            raise ValueError(f"Cannot extract currencies from {value}")

        return pm

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        return str(value)


@st.composite
def PairStringStrategy(draw):
    """
    :param draw:
    :return:


    """
    model = draw(PairStrategy())
    field = PairField()
    return field.serialize("a", {"a": model})


@st.composite
def PairStringAliasStrategy(draw):
    """
    :param draw:
    :return:


    """
    model = draw(PairStrategy())

    field = KCurrencyField()
    # returns random currency aliases...
    base_aliases = field._alias_map.get(model.base.value)
    base_str = base_aliases[random.randint(0, len(base_aliases)-1)]

    quote_aliases = field._alias_map.get(model.quote.value)
    quote_str = quote_aliases[random.randint(0, len(quote_aliases)-1)]
    return base_str + quote_str


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])