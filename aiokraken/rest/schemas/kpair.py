import marshmallow
import typing
from dataclasses import dataclass
from marshmallow import fields, pre_load, post_load

from .base import BaseSchema

from ..exceptions import AIOKrakenException
from ...model.currency import Currency, Fiat, Crypto, Alt


@dataclass(frozen=True)
class PairModel:
    """
    >>> p=PairModel(base=Fiat("EUR"), quote=Crypto("XBT"))
    >>> p.base
    EUR
    >>> p.quote
    XBT
    """

    base: typing.Union[Fiat, Crypto, Alt]
    quote: typing.Union[Fiat, Crypto, Alt]

    def __repr__(self):
        return f"{self.base}/{self.quote}"

    def __str__(self):
        return f"{self.base}{self.quote}"



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
                # TODO : is there a better way ? Overload enum ?
                if value[:i] in Fiat.__members__:
                    p.setdefault(k, Fiat(value[:i]))
                elif value[:i] in Crypto.__members__:
                    p.setdefault(k, Crypto(value[:i]))
                elif value[:i] in Alt.__members__:
                    p.setdefault(k, Alt(value[:i]))
                if value[:i] in [v for v in Fiat.__members__] + [v for v in Crypto.__members__] + [v for v in Alt.__members__]:
                    value = value[i:]
                    i=1
                    break
                else:
                    i+=1

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
