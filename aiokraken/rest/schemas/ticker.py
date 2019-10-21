import typing
import marshmallow
from decimal import Decimal
from marshmallow import fields, pre_load, post_load, validate

from .base import BaseSchema

from ..exceptions import AIOKrakenException
from ...model.ticker import Ticker, DailyValue, MinTrade, MinOrder


class MinOrderField(fields.Field):
    # price = fields.Decimal(as_string=True)
    # whole_lot_volume = fields.Decimal(as_string=True)
    # lot_volume = fields.Decimal(as_string=True)

    def __init__(self, *, as_string=False, **kwargs):
        self.as_string = as_string
        super().__init__(**kwargs)

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

        .. versionchanged:: 2.0.0
            Added ``attr`` and ``data`` parameters.

        .. versionchanged:: 3.0.0
            Added ``**kwargs`` to signature.
        """
        return MinOrder(price=Decimal(value[0]), whole_lot_volume=Decimal(value[1]), lot_volume=Decimal(value[2]))

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        Example: ::

            class TitleCase(Field):
                def _serialize(self, value, attr, obj, **kwargs):
                    if not value:
                        return ''
                    return str(value).title()

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        if self.as_string:
            return [str(v) for v in
                    value]  # WARNING : relies on decimal context (should probably be stored in currency...)
        else:
            return [v for v in value]


class MinTradeField(fields.Field):
    # price= fields.Decimal(as_string=True)
    # lot_volume= fields.Decimal(as_string=True)

    def __init__(self, *, as_string=False, **kwargs):
        self.as_string = as_string
        super().__init__(**kwargs)

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

        .. versionchanged:: 2.0.0
            Added ``attr`` and ``data`` parameters.

        .. versionchanged:: 3.0.0
            Added ``**kwargs`` to signature.
        """
        return MinTrade(price=Decimal(value[0]), lot_volume=Decimal(value[1]))

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        Example: ::

            class TitleCase(Field):
                def _serialize(self, value, attr, obj, **kwargs):
                    if not value:
                        return ''
                    return str(value).title()

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        if self.as_string:
            return [str(v) for v in value]  # WARNING : relies on decimal context (should probably be stored in currency...)
        else:
            return [v for v in value]


class DailyValueField(fields.Field):
    # TODO : different types of numbers ( currency ID | precision: decimal/integer)
    def __init__(self, *, as_string=False, **kwargs):
        self.as_string = as_string
        super().__init__(**kwargs)

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

        .. versionchanged:: 2.0.0
            Added ``attr`` and ``data`` parameters.

        .. versionchanged:: 3.0.0
            Added ``**kwargs`` to signature.
        """
        return DailyValue(today=Decimal(value[0]), last_24_hours=Decimal(value[1]))

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        Example: ::

            class TitleCase(Field):
                def _serialize(self, value, attr, obj, **kwargs):
                    if not value:
                        return ''
                    return str(value).title()

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        if self.as_string:
            return [str(v) for v in value]  # WARNING : relies on decimal context (should probably be stored in currency...)
        else:
            return [v for v in value]


class TickerSchema(BaseSchema):
    # <pair_name> = pair name
    # TODO : namedtuples with nested schema ?
    ask = MinOrderField(data_key='a', as_string=True)  # ask array(<price>, <whole lot volume>, <lot volume>),
    bid = MinOrderField(data_key='b', as_string=True)  #bid array(<price>, <whole lot volume>, <lot volume>),
    last_trade_closed = MinTradeField(data_key='c', as_string=True)  #last trade closed array(<price>, <lot volume>),
    volume = DailyValueField(data_key='v', as_string=True)  #volume array(<today>, <last 24 hours>),
    volume_weighted_average_price = DailyValueField(data_key='p', as_string=True)  #volume weighted average price array(<today>, <last 24 hours>),
    number_of_trades = DailyValueField(data_key='t', as_string=False)  #number of trades array(<today>, <last 24 hours>), # TODO : should be integer, not decimal
    low = DailyValueField(data_key='l', as_string=True)  #low array(<today>, <last 24 hours>),
    high = DailyValueField(data_key='h', as_string=True)  #high array(<today>, <last 24 hours>),
    todays_opening = fields.Decimal(data_key='o', as_string=True)  #today's opening price

    @post_load
    def build_model(self, data, **kwargs):
        return Ticker(**data)

#  a runtime cache of schemas (class !) for different pairs
_pair_ticker_schemas = {}

# TODO : Change that into a class (functor) to have both a call to build instance and a item accessor for the schema/class itself...
def PairTickerSchema(pair):
    """helper function to embed OHLC data frame parsing into a field with any name...
        returns a new instance of the class, creating the class if needed
    """

    def build_model(self, data, **kwargs):
        assert len(data.get('error', [])) == 0  # Errors should have raised exception previously !
        return data.get('pair')


    try:
        return _pair_ticker_schemas[pair]()
    except KeyError:
        _pair_ticker_schemas[pair] = type(f"{pair}_TickerSchema", (BaseSchema,), {
            'pair': marshmallow.fields.Nested(TickerSchema, data_key=pair),
            'make_model': marshmallow.post_load(pass_many=False)(build_model)

        })
    finally:
        return _pair_ticker_schemas[pair]()

