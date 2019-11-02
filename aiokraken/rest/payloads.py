from aiokraken.rest.schemas.kasset import AssetSchema
from aiokraken.rest.schemas.kassetpair import KAssetPairSchema
from aiokraken.rest.schemas.kcurrency import KCurrencyField
from aiokraken.rest.schemas.ohlc import OHLCDataFrameSchema, PairOHLCSchema
from marshmallow import fields, post_load
from .schemas.base import BaseSchema
from .schemas.errors import ErrorsField

from .schemas.kpair import PairField
from .schemas.ticker import TickerSchema


class PayloadBaseSchema(BaseSchema):

    error = ErrorsField()
    # TODO : handle error parsing from payload

    @post_load(pass_many=False)
    def make_result(self, data, **kwargs):
        assert len(data.get('error', [])) == 0  # Errors should have raised exception previously !
        return data.get('result')


class TickerPayloadSchema(PayloadBaseSchema):

    result= fields.Dict(keys = PairField(), values = fields.Nested(TickerSchema))


class AssetPayloadSchema(PayloadBaseSchema):

    result= fields.Dict(keys = KCurrencyField(), values = fields.Nested(AssetSchema))


class AssetPairPayloadSchema(PayloadBaseSchema):

    result= fields.Dict(keys = PairField(), values = fields.Nested(KAssetPairSchema))


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

