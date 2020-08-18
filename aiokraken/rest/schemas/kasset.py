import functools
from dataclasses import dataclass

import typing
from enum import Enum

from marshmallow import fields, post_load, post_dump, pre_load

from aiokraken.rest.schemas.base import BaseSchema

from hypothesis import strategies as st

from ...model.asset import AssetClass, Asset
from ...model.tests.strats.st_asset import AssetClassStrategy, AssetStrategy


class AssetSchema(BaseSchema):
    """
    >>> s= AssetSchema()
    >>> s.load({
    ...    'altname': 'ALTNAME',
    ...    'aclass':  'ACLASS',
    ...    'decimals':  42,
    ...    'display_decimals': 7
    ... })
    KAsset(altname='ALTNAME', aclass='ACLASS', decimals=42, display_decimals=7)
    """
    # name = fields.String()
    altname = fields.String()
    aclass = fields.String()
    decimals = fields.Integer()
    display_decimals = fields.Integer()

    @post_load
    def build_model(self, data, **kwargs):
        a = Asset(altname= data.get('altname'),
                  aclass= data.get('aclass'),
                  decimals= data.get('decimals'),
                  display_decimals = data.get('display_decimals'))
        return a

    @post_dump
    def filter_dict(self, data, **kwargs):
        return data


@st.composite
def KDictStrategy(draw, strategy= AssetStrategy()):
    """
    :param draw:
    :return:


    """
    model = draw(strategy)
    schema = AssetSchema()
    return schema.dump(model)


if __name__ == "__main__":
    import pytest

    pytest.main(["-s", "--doctest-modules", "--doctest-continue-on-failure", __file__])
