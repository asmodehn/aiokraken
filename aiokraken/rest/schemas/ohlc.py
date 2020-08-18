import marshmallow.validate
import typing
import pandas as pd
import numpy as np
from marshmallow import pre_load, post_load, fields
from marshmallow_dataframe import SplitDataFrameSchema
from decimal import Decimal
from collections import namedtuple
import pandas as pd
# import static_frame as sf
from .base import BaseSchema

ohlc_df = pd.DataFrame(
    # Need some sample data to get proper dtypes...
# TODO:   proper Time, proper currencies...
    [[1567039620, '8746.4', '8751.5', '8745.7', '8745.7', '8749.3', '0.09663298', 8],
     [1567039680, '8745.7', '8747.3', '8745.7', '8747.3', '8747.3', '0.00929540', 1]],
    # grab that from kraken documentation
    columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
)

# TODO : manage errors with : https://marshmallow.readthedocs.io/en/stable/extending.html#custom-class-meta-options ???

# Ref : https://stackoverflow.com/questions/42231334/define-fields-programmatically-in-marshmallow-schema


class OHLCField(fields.Field):
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
        # TODO : maybe more checks here on value type / content, maybe conversion, etc.
        # pm = sf.Frame.from_records(records=value,
        pm = pd.DataFrame(data=value,
                          columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
                          # dtypes= # TODO !
        )
        return pm

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


# class KOHLCSchema(BaseSchema):
#     """"""
#     data: fields.List(fields.Nested(OHLCValueSchema()))
#     # columns: OHLCValueSchema
#
#     @pre_load(pass_many=False)
#     def preload(self, data, **kwargs):
#         # cleaning up date into tuples
#         # TODO: more cleaningup /checks /conversion could be done here...
#         return {"data": [OHLCValue(time=ov[0], open=ov[1], high=ov[2], low=ov[3], close=ov[4], vwap=ov[5], volume=ov[6], count=ov[7]) for ov in data],
#                 "index": range(len(data)),
#                 }
#
#     @post_load(pass_many=False)
#     def build_model(self, data, **kwargs):
#         df = pd.DataFrame(data=data,
#                           columns=[c for c in OHLCValue._fields],
#                           index= range(len(data)))  # TODO directly index on time ??
#         return df


# class OHLCDataFrameSchema(SplitDataFrameSchema):
#     """Automatically generated schema for ohlc dataframe"""
#
#     class Meta:
#         dtypes = ohlc_df.dtypes
#
#     @marshmallow.pre_load(pass_many=False)
#     def add_implicit(self, data, **kwargs):
#         try:
#             # dtest = data[0]
#             # test = [pd.to_datetime(dtest[0], unit='s')] + dtest[1:]
#             return {
#                 "data": data, #([pd.to_datetime(d[0], unit='s')] + d[1:] for d in data),
#                 "columns": ohlc_df.columns,
#                 "index": range(len(data)),
#             }
#         except Exception:
#             raise marshmallow.ValidationError("Cannot parse the DataFrame")


#  a runtime cache of schemas (class !) for different pairs
_pair_ohlc_schemas = {}


from ...model.ohlc import OHLC


# TODO : Change that into a class (functor) to have both a call to build instance and a item accessor for the schema/class itself...
def PairOHLCSchema(pair):
    """helper function to embed OHLC data frame parsing into a field with any name...
        returns a new instance of the class, creating the class if needed
    """

    def build_model(self, data, **kwargs):
        assert len(data.get('error', [])) == 0  # Errors should have raised exception previously !
        return OHLC(data=data.get('pair'), last=data.get('last'))


    try:
        return _pair_ohlc_schemas[pair]()
    except KeyError:
        _pair_ohlc_schemas[pair] = type(f"{pair}_OHLCSchema", (BaseSchema,), {
            'pair': OHLCField(data_key=pair),
            'last': marshmallow.fields.Int(),
            'make_model': marshmallow.post_load(pass_many=False)(build_model)

        })
    finally:
        return _pair_ohlc_schemas[pair]()

