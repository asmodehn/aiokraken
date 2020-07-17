import functools
import time
import typing
from marshmallow import fields
from hypothesis import strategies as st


class TMModel:

    def __init__(self, value: int, relative: bool=True):
        # Note : this can accept past times...
        # casting to prevent later problems...
        self.relative = bool(relative)
        self.value = int(value)

    def __repr__(self):
        return str(self)

    def __str__(self)-> str:
        return ("+" if self.relative else "") + str(self.value)

    def __bool__(self) -> bool:
        # truthy if meaningful ( != not expired )
        if self.relative:
            return self.value > 0
        else:
            return bool(self.value)  # any value here is meaningful

    def expired(self) -> bool:
        if self.relative:
            return self.value <= 0  # TODO This requires a reference time...
        else:
            return self.value > int(time.time())


# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
TMStrategy = functools.partial(st.one_of, st.builds(TMModel, value=st.integers(min_value=0), relative=st.sampled_from([True])),
                                          st.builds(TMModel, value=st.integers(min_value=int(time.time())), relative=st.sampled_from([False])))


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
        # return TMModel(value, relative=False)
        return value  # TMModel seems to prevent easy casting to proper time later... do we really need it for parsing ??

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        if value is not None:
            return str(value)
        else:
            return ''  # meaningless string value


@st.composite
def TimerStringStrategy(draw):
    model = draw(TMStrategy())
    field = TimerField()
    return field.serialize('a', {'a': model})

