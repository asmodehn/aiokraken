import functools
import hypothesis.strategies as st
import typing
from marshmallow import fields


class Leverage:
    a: int
    b: int

    def __init__(self, a: int, b: int):
        self.a = a
        self.b = b

    def __repr__(self):
        return f"<Lvrg {self.a}:{self.b}>"

    def __str__(self):
        return f"{self.a}:{self.b}"


# Using partial call here to delay evaluation (and get same semantics as potentially more complex strategies)
LeverageStrategy = functools.partial(st.builds, Leverage,
                             a=st.integers(min_value=0, max_value=50),
                             b=st.integers(min_value=0, max_value=50))


class LeverageField(fields.Field):
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
        a, b = value.split(':')
        return Leverage(int(a), int(b))

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
            return 'none'  # meaningless string value


@st.composite
def LeverageStringStrategy(draw):
    model = draw(LeverageStrategy())
    field = LeverageField()
    return field.serialize('a', {'a': model})
