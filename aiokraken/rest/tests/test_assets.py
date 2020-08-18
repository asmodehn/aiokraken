import unittest

from hypothesis import given

from aiokraken.rest.assets import Assets

from aiokraken.rest.tests.strats.st_assets import st_assets


class TestAssets(unittest.TestCase):

    @given(assets=st_assets())
    def test_valid(self, assets):
        assert isinstance(assets, Assets)

        # unicity of restname
        restnames = {p.restname for p in assets.values()}
        assert len(restnames) == len(assets)

        # TODO : add more properties tests
