import typing

from enum import (IntEnum)

from marshmallow import fields

if __package__:
    from ...utils.stringenum import StringEnum
else:
    from aiokraken.utils.stringenum import StringEnum


class KOrderTypeModel(StringEnum):
    """

    Accepts transparently strings

    >>> KOrderTypeModel('market')
    market
    >>> str(KOrderTypeModel('limit'))
    'limit'

    rejects anything else:

    >>> KOrderTypeModel('what is this')
    Traceback (most recent call last):
        ...
    ValueError: 'what is this' is not a valid KTypeModel

    """
    market = 'market'
    limit = 'limit'
    stop_loss = 'stop-loss'
    take_profit = 'take-profit'
    stop_loss_profit = 'stop-loss-profit'
    stop_loss_profit_limit = 'stop-loss-profit-limit'
    stop_loss_limit = 'stop-loss-limit'
    take_profit_limit = 'take-profit-limit'
    trailing_stop = 'trailing-stop'
    trailing_stop_limit = 'trailing-stop-limit'
    stop_loss_and_limit = 'stop-loss-and-limit'
    settle_position = 'settle-position'


class KOrderTypeField(fields.Field):
    """
    A field to interface with marshmallow

    >>> KOrderTypeField().serialize('take-profit', obj=KOrderTypeModel('take-profit'))
    'take-profit'
    >>> KOrderTypeField().deserialize('take-profit')
    take-profit

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
        return KOrderTypeModel(value)

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


if __name__ == "__main__":
    import pytest
    pytest.main(['-s', '--doctest-modules', '--doctest-continue-on-failure', __file__])
