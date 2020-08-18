import functools
from datetime import datetime, timedelta, timezone

import time
import typing
from marshmallow import fields
from hypothesis import strategies as st

# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
# TODO : maybe we also need floats here ??
RelativeTimeStrategy = functools.partial(st.timedeltas, min_value=timedelta(seconds=0))
AbsoluteTimeStrategy = st.datetimes
TimeStrategy = functools.partial(st.one_of, AbsoluteTimeStrategy(), RelativeTimeStrategy())


class TimerField(fields.Field):
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
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        elif isinstance(value, str):
            if value.startswith('+'):  # relative from now as a timedelta
                return timedelta(seconds=float(value[1:]))
            else:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
        else:
            raise NotImplementedError

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """

        if isinstance(value, datetime):
            return datetime.timestamp(value)  # outputting timestamp
        elif isinstance(value, timedelta):
            return f"+{value.total_seconds()}"  # outputting str

@st.composite
def RelativeTimeSerializedStrategy(draw):
    model = draw(RelativeTimeStrategy())
    field = TimerField()
    return field.serialize('a', {'a': model})


@st.composite
def AbsoluteTimeSerializedStrategy(draw):
    model = draw(AbsoluteTimeStrategy())
    field = TimerField()
    return field.serialize('a', {'a': model})
