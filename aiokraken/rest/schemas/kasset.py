from dataclasses import dataclass

from marshmallow import fields, post_load, post_dump

from aiokraken.rest.schemas.base import BaseSchema


from hypothesis import strategies as st

@dataclass
class KAsset:

    altname: str  # alternate name
    aclass: str  # asset class
    decimals: int  # scaling decimal places for record keeping
    display_decimals: int  # scaling decimal places for output display


@st.composite
def KAssetStrategy(draw):

    return KAsset(
        altname= draw(st.text(max_size=5)),
        aclass = draw(st.text(max_size=5)),
        decimals= draw(st.integers()),
        display_decimals= draw(st.integers())
    )


class AssetSchema(BaseSchema):

    altname = fields.String()
    aclass = fields.String()
    decimals = fields.Integer()
    display_decimals = fields.Integer()

    @post_load
    def build_model(self, data, **kwargs):
        a = KAsset(altname= data.get('altname'),
                   aclass= data.get('aclass'),
                   decimals= data.get('decimals'),
                   display_decimals = data.get('display_decimals'))
        return a

    @post_dump
    def filter_dict(self, data, **kwargs):
        return data


@st.composite
def KDictStrategy(draw, strategy= KAssetStrategy()):
    """
    :param draw:
    :return:


    """
    model = draw(strategy)
    schema = AssetSchema()
    return schema.dump(model)
