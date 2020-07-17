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
        assetpairs = await rest_kraken.retrieve_assetpairs(pairs=["XBTEUR"])
        pair = assetpairs["XXBTZEUR"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{assetpairs}')

        assert isinstance(pair, AssetPair)


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs_oldstr():
    """ get kraken assetpairs"""
    async with RestClient(server=Server()) as rest_kraken:
        assetpairs = await rest_kraken.retrieve_assetpairs(pairs=["XXBTZEUR"])
        pair = assetpairs["XXBTZEUR"]  # PB : convert between representations of currency ? => job of the domain model layer
        print(f'response is \n{assetpairs}')

        assert isinstance(pair, AssetPair)

# TODO : test updating partial/ old assetpair


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs_all():
    """ get kraken assetpairs"""
    async with RestClient(server=Server()) as rest_kraken:
        assetpairs = await rest_kraken.retrieve_assetpairs()
        print(f'response is \n{assetpairs}')
        for name, asset in assetpairs.items():
            assert isinstance(asset, AssetPair)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
