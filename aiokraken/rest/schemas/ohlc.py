import marshmallow.validate
import typing
import pandas as pd
import numpy as np
from marshmallow_dataframe import SplitDataFrameSchema
from decimal import Decimal

from .base import BaseSchema

ohlc_df = pd.DataFrame(
    # Need some sample data to get proper dtypes...
# TODO:    [[1567039620, Decimal('8746.4'), Decimal('8751.5'), Decimal('8745.7'), Decimal('8745.7'), Decimal('8749.3'), Decimal('0.09663298'), 8],
    [[1567039620, '8746.4', '8751.5', '8745.7', '8745.7', '8749.3', '0.09663298', 8],
     [1567039680, '8745.7', '8747.3', '8745.7', '8747.3', '8747.3', '0.00929540', 1]],
    # grab that from kraken documentation
    columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
)

# TODO : manage errors with : https://marshmallow.readthedocs.io/en/stable/extending.html#custom-class-meta-options ???

# Ref : https://stackoverflow.com/questions/42231334/define-fields-programmatically-in-marshmallow-schema

class OHLCDataFrameSchema(SplitDataFrameSchema):
    """Automatically generated schema for ohlc dataframe"""

    class Meta:
        dtypes = ohlc_df.dtypes

    @marshmallow.pre_load(pass_many=False)
    def add_implicit(self, data, **kwargs):
        try:
            return {
                "data": data,
                "columns": ohlc_df.columns,
                "index": range(len(data)),
            }
        except Exception:
            raise marshmallow.ValidationError("Cannot parse the DataFrame")

    # load or dump ?
    # @marshmallow.post_load(pass_many=False)
    # def make_ohlc(self, data, **kwargs):
    #     return data  # TODO : embed in a specific type. all dataframes are not equivalent...


#  a runtime cache of schemas (class !) for different pairs
_pair_ohlc_schemas = {}


# TODO : Change that into a class (functor) to have both a call to build instance and a item accessor for the schema/class itself...
def PairOHLCSchema(pair):
    """helper function to embed OHLC data frame parsing into a field with any name...
        returns a new instance of the class, creating the class if needed
    """
    try:
        return _pair_ohlc_schemas[pair]()
    except KeyError:
        _pair_ohlc_schemas[pair] = type(f"{pair}_OHLCSchema", (BaseSchema,), {
            pair: marshmallow.fields.Nested(OHLCDataFrameSchema),
            'last': marshmallow.fields.Int()
        })
    finally:
        return _pair_ohlc_schemas[pair]()

