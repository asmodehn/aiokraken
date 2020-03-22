import unittest

from hypothesis import given

from aiokraken.rest.assetpairs import AssetPairs

from aiokraken.rest.tests.strats.st_assetpairs import st_assetpairs


class TestAssetPairs(unittest.TestCase):

    @given(assetpairs=st_assetpairs())
    def test_valid(self, assetpairs):
        assert isinstance(assetpairs, AssetPairs)

        # TODO : add more properties tests
