import unittest

from hypothesis import given

from aiokraken.rest.assetpairs import AssetPairs

from aiokraken.rest.tests.strats.st_assetpairs import st_assetpairs


class TestAssetPairs(unittest.TestCase):

    @given(assetpairs=st_assetpairs())
    def test_valid(self, assetpairs):
        assert isinstance(assetpairs, AssetPairs)

        # unicity of wsname
        wsnames = {p.wsname for p in assetpairs.values()}
        assert len(wsnames) == len(assetpairs)

        # unicity of restname
        restnames = {p.restname for p in assetpairs.values()}
        assert len(restnames) == len(assetpairs)

        # TODO : add more properties tests
