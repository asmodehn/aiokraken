import unittest

from hypothesis import given, settings, Verbosity

from aiokraken.model.tests.strats.st_asset import AssetStrategy


class TestAsset(unittest.TestCase):

    # @settings(verbosity=Verbosity.verbose)
    @given(AssetStrategy())
    def test_model(self, model):
        assert isinstance(model.altname, str)
        assert isinstance(model.aclass, str)
        assert isinstance(model.decimals, int)
        assert isinstance(model.display_decimals, int)
