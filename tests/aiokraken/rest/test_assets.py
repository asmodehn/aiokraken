import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.kasset import Asset


# TODO : test multiple assets... multiple ways...


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_newstr():
    """ get kraken assets"""
    async with RestClient(server=Server()) as rest_kraken:
        asset_run = rest_kraken.assets(assets=["XBT"])
        response = await asset_run()
        asset = response["XXBT"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{response}')

        assert isinstance(asset, Asset)


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_oldstr():
    """ get kraken assets"""
    async with RestClient(server=Server()) as rest_kraken:
        asset_run = rest_kraken.assets(assets=["XXBT"])
        response = await asset_run()
        asset = response["XXBT"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{response}')

        assert isinstance(asset, Asset)



@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_all():
    """ get kraken assets"""
    async with RestClient(server=Server()) as rest_kraken:
        asset_run = rest_kraken.assets()
        response = await asset_run()
        print(f'response is \n{response}')
        for name, asset in response.items():
            assert isinstance(asset, Asset)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])