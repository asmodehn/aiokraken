


# in Minutes : 1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600
import functools
from datetime import timedelta
from enum import Enum

import typing
from hypothesis import strategies as st
from marshmallow import fields


# Enums to store accepted strings.
# Unknown strings will be ignored
class KTimeFrameModel(Enum):
    """
    Accepts transparently strings
    >>> KTimeFrameModel(30)
    <KTimeFrameModel.thirty_minutes: 30>
    >>> str(KTimeFrameModel(30))
    'thirty_minutes'

    Does not accept anything else
    >>> KTimeFrameModel(72)
    Traceback (most recent call last):
        ...
    ValueError: 72 is not a valid KTimeFrameModel

    """

    one_minute = 1
    five_minutes = 5
    fifteen_minutes = 15
    thirty_minutes = 30
    half_an_hour = 30
    sixty_minutes = 60
    one_hour = 60
    four_hours = 240
    one_day = 1440
    twenty_four_hours = 1440
    seven_days = 10080
    fifteen_days = 21600

    def secs(self):
        return self.value * 60

    def to_timedelta(self):
        return timedelta(minutes=self.value)

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value


# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
KTimeFrameStrategy = functools.partial(st.sampled_from, KTimeFrameModel)


class KTimeFrameField(fields.Field):
    """
    A field to interface with marshmallow

    >>> KTimeFrameField().serialize('v', obj={ 'v': KTimeFrameModel(15)})
    15
    >>> KTimeFrameField().deserialize(15)
    <KTimeFrameModel.fifteen_minutes: 15>

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
        return KTimeFrameModel(value)

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        return int(value)


@st.composite
def KTimeFrameStringStrategy(draw):
    model = draw(KTimeFrameStrategy())
    field = KTimeFrameField()
    return field.serialize("a", {"a": model})


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
