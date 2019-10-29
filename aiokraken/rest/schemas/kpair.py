import marshmallow
import typing
from dataclasses import dataclass

from marshmallow import fields, pre_load, post_load

if not __package__:
    __package__ = 'aiokraken.rest.schemas'

from .base import BaseSchema
from ..exceptions import AIOKrakenException
from .kcurrency import KCurrency, KCurrencyStrategy
from hypothesis import given, strategies as st


@dataclass(frozen=True)
class PairModel:
    """
    >>> p=PairModel(base=KCurrency("XBT"), quote=KCurrency("EUR"))
    >>> p.base
    XBT
    >>> p.quote
    EUR
    """

    base: KCurrency
    quote: KCurrency

    # def __post_init__(self):
    #     if self.base == self.quote:
    #         raise ValueError(f"Pair cannot have base {self.base} and quote {self.quote}")

    def __repr__(self):
        return f"{repr(self.base)}/{repr(self.quote)}"

    def __str__(self):
        # or using .value ?? see other stringenums like ordertype...
        return f"{self.base}{self.quote}"

@st.composite
def PairStrategy(draw):
    """

    :param draw:
    :return:

    """
    base = draw(KCurrencyStrategy())
    quote= draw(KCurrencyStrategy().filter(lambda c: c != base))
    return PairModel(base=base, quote=quote)


# This makes hypothesis blow up because of inability to shrink...
# @st.composite
# def PairStrategy(draw, base=KCurrencyStrategy(), quote=KCurrencyStrategy()):
#     b = draw(base)
#     q = draw(quote)
#     while q == b:
#         q = draw(quote)
#     return PairModel(base=b, quote=q)


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
                    p.setdefault(k, KCurrency(iv[:i]))
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


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])