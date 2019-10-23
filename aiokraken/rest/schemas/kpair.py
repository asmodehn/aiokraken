import marshmallow
import typing
from dataclasses import dataclass
from marshmallow import fields, pre_load, post_load

from .base import BaseSchema

from ..exceptions import AIOKrakenException
from .kcurrency import KCurrency, KCurrencyStrategy
from hypothesis import given, strategies as st


@dataclass(frozen=True)
class PairModel:
    """
    >>> p=PairModel(base=KCurrency("EUR"), quote=KCurrency("XBT"))
    >>> p.base
    EUR
    >>> p.quote
    XBT
    """

    base: KCurrency
    quote: KCurrency

    def __repr__(self):
        return f"{repr(self.base)}/{repr(self.quote)}"

    def __str__(self):
        # or using .value ?? see other stringenums like ordertype...
        return f"{self.base}{self.quote}"


def PairStrategy(base=KCurrencyStrategy(), quote=KCurrencyStrategy()):
    return st.builds(PairModel, base=base, quote=quote)


class PairField(fields.Field):
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
        # TODO : proper Pair parsing !!!
        p = {}
        i=1
        for k in ['base', 'quote']:
            while i <= len(value):
                # some kind of pattern matching... for python 3.7
                # TODO : is there a better way ? Overload enum ? try/except ?
                # Ref : https://pypi.org/project/algebraic-data-types/
                # Ref : https://github.com/python/mypy/issues/2464

                try:
                    p.setdefault(k, KCurrency(value[:i]))
                    value = value[i:]
                    i=1
                    break
                except Exception as e:
                    i += 1

        return PairModel(base=p['base'], quote=p['quote'])

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
def PairStringStrategy(draw,base=KCurrencyStrategy(), quote=KCurrencyStrategy()):
    model = draw(PairStrategy(base=base, quote=quote))
    field = PairField()
    return field.serialize('a', {'a': model})
