import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient


# TODO : test multiple assets... multiple ways...
from aiokraken.model.assetpair import AssetPair


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs_newstr():
    """ get kraken assetpairs"""
    async with RestClient(server=Server()) as rest_kraken:
        assetpairs_run = rest_kraken.retrieve_assetpairs(pairs=["XBTEUR"])
        response = await assetpairs_run()
        asset = response["XXBTZEUR"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{response}')

        assert isinstance(asset, AssetPair)


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs_oldstr():
    """ get kraken assetpairs"""
    async with RestClient(server=Server()) as rest_kraken:
        assetpairs_run = rest_kraken.retrieve_assetpairs(pairs=["XXBTZEUR"])
        response = await assetpairs_run()
        asset = response["XXBTZEUR"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{response}')

        assert isinstance(asset, AssetPair)

# TODO : test updating partial/ old assetpair

@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs_all():
    """ get kraken assetpairs"""
    async with RestClient(server=Server()) as rest_kraken:
        assetpairs_run = rest_kraken.retrieve_assetpairs()
        response = await assetpairs_run()
        print(f'response is \n{response}')
        for name, asset in response.items():
            assert isinstance(asset, AssetPair)



if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
