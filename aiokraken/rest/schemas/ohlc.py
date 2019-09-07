import marshmallow.validate
import typing
import pandas as pd
import numpy as np
from marshmallow_dataframe import SplitDataFrameSchema
from decimal import Decimal
import pandas as pd
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

class OHLCDataFrameSchema(SplitDataFrameSchema):
    """Automatically generated schema for ohlc dataframe"""

    class Meta:
        dtypes = ohlc_df.dtypes

    @marshmallow.pre_load(pass_many=False)
    def add_implicit(self, data, **kwargs):
        try:
            # dtest = data[0]
            # test = [pd.to_datetime(dtest[0], unit='s')] + dtest[1:]
            return {
                "data": data, #([pd.to_datetime(d[0], unit='s')] + d[1:] for d in data),
                "columns": ohlc_df.columns,
                "index": range(len(data)),
            }
        except Exception:
            raise marshmallow.ValidationError("Cannot parse the DataFrame")

    # @marshmallow.post_load(pass_many=False)
    # def convert(self, data, **kwargs):
    #     try:
    #         data = data.time.apply(lambda d: pd.to_datetime(d, unit='s'))
    #         return data
    #     except Exception:
    #         raise marshmallow.ValidationError("Cannot convert dataframe contents")


    # load or dump ?
    # @marshmallow.post_load(pass_many=False)
    # def make_ohlc(self, data, **kwargs):
    #     return data  # TODO : embed in a specific type. all dataframes are not equivalent...


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
            'pair': marshmallow.fields.Nested(OHLCDataFrameSchema, data_key=pair),
            'last': marshmallow.fields.Int(),
            'make_model': marshmallow.post_load(pass_many=False)(build_model)

        })
    finally:
        return _pair_ohlc_schemas[pair]()

