import unittest

from aiokraken.rest.schemas.kasset import Asset, AssetStrategy, AssetSchema, KDictStrategy
from hypothesis import given, settings, Verbosity

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestKAssetSchema(unittest.TestCase):

    def setUp(self) -> None:
        self.schema = AssetSchema()

    #@settings(verbosity=Verbosity.verbose)
    @given(
        KDictStrategy(AssetStrategy()))
    def test_deserialize(self, modeldict):
        a = self.schema.load(modeldict)
        assert isinstance(a, Asset)

    #@settings(verbosity=Verbosity.verbose)
    @given(AssetStrategy())
    def test_serialize(self, model):
        a = self.schema.dump(model)
        assert 'altname' in a
        assert 'aclass' in a
        assert 'decimals' in a
        assert 'display_decimals' in a