import decimal
from dataclasses import dataclass

import typing
from hypothesis import strategies as st
from marshmallow import fields, post_load, post_dump
from marshmallow.schema import BaseSchema

from aiokraken.rest.schemas import KCurrency
from aiokraken.rest.schemas.kasset import KAssetStrategy, KAssetClass
from aiokraken.rest.schemas.kcurrency import KCurrencyField


@dataclass
class VolumeFee:
    volume: decimal.Decimal  # unit ??
    fee: decimal.Decimal  # pct



class VolumeFeeField(fields.Field):
    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]],
        **kwargs,
    ):
        """Deserialize value. Concrete :class:`Field` classes should implement this method.

        :param value: The value to be deserialized.
        :param attr: The attribute/key in `data` to be deserialized.
        :param data: The raw input data passed to the `Schema.load`.
        :param kwargs: Field-specific keyword arguments.
        :raise ValidationError: In case of formatting or validation failure.
        :return: The deserialized value.

        """
        return VolumeFee(*value)

    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        """Serializes ``value`` to a basic Python datatype. Noop by default.
        Concrete :class:`Field` classes should implement this method.

        :param value: The value to be serialized.
        :param str attr: The attribute or key on the object to be serialized.
        :param object obj: The object the value was pulled from.
        :param dict kwargs: Field-specific keyword arguments.
        :return: The serialized value
        """
        # TODO : manage that to list / str of list / via simplejson ??
        return str([value.volume, value.fee])


@dataclass
class KAssetPair:

    altname: str  # alternate pair name
    wsname: str   # WebSocket pair name (if available)
    aclass_base: KAssetClass  # asset class of base component
    base: KCurrency  # asset id of base component
    aclass_quote: str  # asset class of quote component
    quote: KCurrency  # asset id of quote component
    lot: str  # volume lot size
    pair_decimals: int  # scaling decimal places for pair
    lot_decimals: int  # scaling decimal places for volume
    lot_multiplier: int  # amount to multiply lot volume by to get currency volume
    leverage_buy: list  # array of leverage amounts available when buying
    leverage_sell: list  # array of leverage amounts available when selling
    fees: list  # fee schedule array in [volume, percent fee] tuples
    fees_maker: list  # maker fee schedule array in [volume, percent fee] tuples (if on maker/taker)
    fee_volume_currency: KCurrency  # volume discount currency
    margin_call: int  # margin call level
    margin_stop: int  # stop-out/liquidation margin level


@st.composite
def KAssetPairStrategy(draw):

    return KAssetPair(
        altname= draw(st.text(max_size=5)),
        wsname= draw(st.text(max_size=5)),

        aclass_base = draw(KAssetStrategy()),
        base = draw(st.text(max_size=5)),
        aclass_quote = draw(KAssetStrategy()),
        quote = draw(st.text(max_size=5)),

        lot = draw(st.decimals(allow_nan=False, allow_infinity=False)),
        pair_decimals= draw(st.integers(max_value=255)),
        lot_decimals= draw(st.integers(max_value=255)),
        lot_multiplier= draw(st.integers(max_value=255)),

        leverage_buy=draw(st.lists(st.integers(max_value=255), max_size=5 )),
        leverage_sell= draw(st.lists(st.integers(max_value=255), max_size=5 )),

        fees = draw(st.lists(st.integers(max_value=255), max_size=5 )),
        fees_maker = draw(st.lists(st.integers(max_value=255), max_size=5 )),
        fee_volume_currency = draw(st.lists(st.integers(max_value=255), max_size=5 )),

        margin_call = draw(st.integers(max_value=255)),
        margin_stop = draw(st.integers(max_value=255))

    )


class KAssetPairSchema(BaseSchema):
    """
    >>> s= KAssetPairSchema()
    >>> s.load({
    ...    "altname": "str",  # alternate pair name
    ...    "wsname": "str",   # WebSocket pair name (if available)
    ...    "aclass_base": "str",  # asset class of base component
    ...    "base": "str",  # asset id of base component
    ...    "aclass_quote": "str",  # asset class of quote component
    ...    "quote": "str",  # asset id of quote component
    ...    "lot": "int",  # volume lot size
    ...    "pair_decimals": "int",  # scaling decimal places for pair
    ...    "lot_decimals": "int",  # scaling decimal places for volume
    ...    "lot_multiplier": "int",  # amount to multiply lot volume by to get currency volume
    ...    "leverage_buy": "int",  # array of leverage amounts available when buying
    ...    "leverage_sell": "int",  # array of leverage amounts available when selling
    ...    "fees": "str",  # fee schedule array in [volume, percent fee] tuples
    ...    "fees_maker": "str",  # maker fee schedule array in [volume, percent fee] tuples (if on maker/taker)
    ...    "fee_volume_currency": "str",  # volume discount currency
    ...    "margin_call": "str",  # margin call level
    ...    "margin_stop": "str"  # stop-out/liquidation margin level
    ... })
    """
    # name = fields.String()
    altname = fields.String()  # alternate pair name
    wsname= fields.String()  # WebSocket pair name (if available)
    aclass_base= fields.String()  # asset class of base component
    base= fields.String()  # asset id of base component
    aclass_quote= fields.String()  # asset class of quote component
    quote= fields.String()  # asset id of quote component
    lot= fields.String()  # volume lot size
    pair_decimals= fields.Integer() # scaling decimal places for pair
    lot_decimals= fields.Integer() # scaling decimal places for volume
    lot_multiplier= fields.Integer() # amount to multiply lot volume by to get currency volume
    leverage_buy= fields.List(fields.Integer())   # array of leverage amounts available when buying
    leverage_sell= fields.List(fields.Integer())   # array of leverage amounts available when selling
    fees=fields.List(VolumeFeeField())  # fee schedule array in [volume, percent fee] tuples
    fees_maker=fields.List(VolumeFeeField())  # maker fee schedule array in [volume, percent fee] tuples (if on maker/taker)
    fee_volume_currency=KCurrencyField()  # volume discount currency
    margin_call= fields.Integer()  # margin call level
    margin_stop= fields.Integer()  # stop-out/liquidation margin level

    @post_load
    def build_model(self, data, **kwargs):
        a = KAssetPair(altname= data.get('altname'),
            wsname = data.get('wsname'),  # WebSocket pair name (if available)
            aclass_base = data.get('aclass_base'),  # asset class of base component
            base = data.get('base'),  # asset id of base component
            aclass_quote = data.get('aclass_quote'),  # asset class of quote component
            quote = data.get('quote'),  # asset id of quote component
            lot = data.get('lot'),  # volume lot size
            pair_decimals = data.get('pair_decimals'),  # scaling decimal places for pair
            lot_decimals = data.get('lot_decimals'),  # scaling decimal places for volume
            lot_multiplier = data.get('lot_multiplier'),  # amount to multiply lot volume by to get currency volume
            leverage_buy = data.get('leverage_buy'),  # array of leverage amounts available when buying
            leverage_sell = data.get('leverage_sell'),  # array of leverage amounts available when selling
            fees = data.get('fees'),  # fee schedule array in [volume, percent fee] tuples
            fees_maker = data.get('fees_maker'),  # maker fee schedule array in [volume, percent fee] tuples (if on maker/taker)
            fee_volume_currency = data.get('fee_volume_currency'),  # volume discount currency
            margin_call = data.get('margin_call'),  # margin call level
            margin_stop = data.get('margin_stop'),  # stop-out/liquidation margin level
        )
        return a

    @post_dump
    def filter_dict(self, data, **kwargs):
        return data


@st.composite
def KDictStrategy(draw, strategy= KAssetPairStrategy()):
    """
    :param draw:
    :return:


    """
    model = draw(strategy)
    schema = KAssetPairSchema()
    return schema.dump(model)



if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
