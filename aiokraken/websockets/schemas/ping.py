import functools
import typing
from enum import Enum

from marshmallow import fields
from hypothesis import given, strategies as st

# TODO : solve this to use local file, not installed one...
# if __package__:
#     from ...utils.stringenum import StringEnum
# else:
from aiokraken.utils.stringenum import StringEnum


# Enums to store accepted strings.
# Unknown strings will be rejected
class KPingModel(StringEnum):
    """
    Accepts transparently strings
    >>> KPingModel('ping')
    ping
    >>> str(KPingModel('ping'))
    'ping'

    Does not accept anything else
    >>> KPingModel('something')
    Traceback (most recent call last):
        ...
    ValueError: 'something' is not a valid KPingModel

    """

    ping = "ping"


# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
KPingStrategy = functools.partial(st.sampled_from, KPingModel)


class KPingField(fields.Field):
    """
    A field to interface with marshmallow

    >>> KPingField().serialize('ping', obj=KPingModel('ping'))
    'ping'
    >>> KPingField().deserialize('ping')
    ping

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
        return KPingModel(value)

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
def KPingStringStrategy(draw):
    model = draw(KPingStrategy())
    field = KPingField()
    return field.serialize("a", {"a": model})


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
