import time
import unittest
from decimal import Decimal

from parameterized import parameterized
import json
import marshmallow
import decimal

from aiokraken.rest.schemas.kasset import KAsset, KAssetStrategy, AssetSchema, KDictStrategy
from ..kabtype import KABTypeModel, KABTypeField, KABTypeStrategy, KABTypeStringStrategy
from ...exceptions import AIOKrakenException
from hypothesis import given, settings, Verbosity

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestKAsset(unittest.TestCase):

    #@settings(verbosity=Verbosity.verbose)
    @given(KAssetStrategy())
    def test_model(self, model):
        assert isinstance(model.altname, str)
        assert isinstance(model.aclass, str)
        assert isinstance(model.decimals, int)
        assert isinstance(model.display_decimals, int)


class TestKAssetSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = AssetSchema()

    #@settings(verbosity=Verbosity.verbose)
    @given(
        KDictStrategy( KAssetStrategy()))
    def test_deserialize(self, modeldict):
        a = self.schema.load(modeldict)
        assert isinstance(a, KAsset)

    #@settings(verbosity=Verbosity.verbose)
    @given(KAssetStrategy())
    def test_serialize(self, model):
        a = self.schema.dump(model)
        assert 'altname' in a
        assert 'aclass' in a
        assert 'decimals' in a
        assert 'display_decimals' in a