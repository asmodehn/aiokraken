import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.asset import Asset


# TODO : test multiple assets... multiple ways...


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_newstr():
    """ get kraken assets"""
    async with RestClient(server=Server()) as rest_kraken:
        assets = await rest_kraken.retrieve_assets(assets=["XBT"])
        asset = assets["XXBT"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{assets}')

        assert isinstance(asset, Asset)


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_oldstr():
    """ get kraken assets"""
    async with RestClient(server=Server()) as rest_kraken:
        assets = await rest_kraken.retrieve_assets(assets=["XXBT"])
        asset = assets["XXBT"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{assets}')

        assert isinstance(asset, Asset)

# TODO : test updating partial/old asset


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_all():
    """ get kraken assets"""
    async with RestClient(server=Server()) as rest_kraken:
        assets = await rest_kraken.retrieve_assets()
        print(f'response is \n{assets}')
        for name, asset in assets.items():
            assert isinstance(asset, Asset)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])