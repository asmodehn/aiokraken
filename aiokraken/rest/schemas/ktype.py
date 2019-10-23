import functools
import typing
from enum import Enum

from marshmallow import fields
from hypothesis import given, strategies as st


if __package__:
    from ...utils.stringenum import StringEnum
else:
    from aiokraken.utils.stringenum import StringEnum


# Enums to store accepted strings.
# Unknown strings will be ignored
class KTypeModel(StringEnum):
    """
    Accepts transparently strings
    >>> KTypeModel('sell')
    sell
    >>> str(KTypeModel('sell'))
    'sell'

    >>> KTypeModel('buy')
    buy
    >>> str(KTypeModel('buy'))
    'buy'

    Does not accept anything else
    >>> KTypeModel('something')
    Traceback (most recent call last):
        ...
    ValueError: 'something' is not a valid KTypeModel

    """
    buy = 'buy'
    sell = 'sell'


# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
KTypeStrategy = functools.partial(st.sampled_from, KTypeModel)


class KTypeField(fields.Field):
    """
    A field to interface with marshmallow

    >>> KTypeField().serialize('buy', obj=KTypeModel('buy'))
    'buy'
    >>> KTypeField().deserialize('buy')
    buy

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
        return KTypeModel(value)

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
def KTypeStringStrategy(draw):
    model = draw(KTypeStrategy())
    field = KTypeField()
    return field.serialize('a', {'a': model})


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
