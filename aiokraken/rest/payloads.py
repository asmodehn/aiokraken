from aiokraken.rest.schemas.kledger import KLedgerInfoSchema

from aiokraken.rest.schemas.kasset import AssetSchema
from aiokraken.rest.schemas.kassetpair import KAssetPairSchema
from aiokraken.rest.schemas.ohlc import PairOHLCSchema
from marshmallow import fields, post_load
from .schemas.base import BaseSchema
from .schemas.errors import ErrorsField

from .schemas.ticker import TickerSchema


class PayloadBaseSchema(BaseSchema):

    error = ErrorsField()
    # TODO : handle error parsing from payload

    @post_load(pass_many=False)
    def make_result(self, data, **kwargs):
        assert len(data.get('error', [])) == 0  # Errors should have raised exception previously !
        return data.get('result')


class TickerPayloadSchema(PayloadBaseSchema):
    # Note : Only getting strings from the network, not attempting to validate all assets
    #  => requires human understanding and should probably be part of a "formal" modeling layer instead...
    result= fields.Dict(keys = fields.String(), values = fields.Nested(TickerSchema))


class AssetPayloadSchema(PayloadBaseSchema):

    result= fields.Dict(keys = fields.String(), values = fields.Nested(AssetSchema))

    @post_load()
    def register_name(self, data, many, partial):
        for n in data.keys():
            data[n] = data[n](restname=n)
        return data


class AssetPairPayloadSchema(PayloadBaseSchema):

    result= fields.Dict(keys = fields.String(), values = fields.Nested(KAssetPairSchema))

    @post_load()
    def register_name(self, data, many, partial):
        for n in data.keys():
            data[n] = data[n](restname=n)
        return data


# Ref : https://stevenloria.com/dynamic-schemas-in-marshmallow/
# BUGGY ! TODO : Fix it ! It should help to simplify our code...
def OHLCPayloadSchema(pair):
    # TODO : improve...
    #  Do we need to optimize with a cache storage or is it just useless complexity ?
    #  Is there a way to make that more "static", yet check as possible the data dynamically ??

    # A less scary call to type()
    return PayloadBaseSchema.from_dict({
        'result': fields.Nested(PairOHLCSchema(pair)),
    })

