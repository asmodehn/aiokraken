import pytest

from aiokraken.rest.schemas import PairModel, KCurrency
from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.kasset import KAsset


# TODO : test multiple assets... multiple ways...

@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_model():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.assets(assets=[KCurrency.XBT])
        asset = response[KCurrency.XBT]
        print(f'response is \n{response}')

        assert isinstance(asset, KAsset)

    finally:
        await rest_kraken.close()


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_newstr():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.assets(assets=["XBT"])
        asset = response[KCurrency.XBT]  # PB : convert between representations of currency ?
        print(f'response is \n{response}')

        assert isinstance(asset, KAsset)

    finally:
        await rest_kraken.close()


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_oldstr():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.assets(assets=["XXBT"])
        asset = response[KCurrency.XBT]  # PB : convert between representations of currency ?
        print(f'response is \n{response}')

        assert isinstance(asset, KAsset)

    finally:
        await rest_kraken.close()



@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_asset_all():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.assets()
        print(f'response is \n{response}')
        for asset in response:
            assert isinstance(asset, KAsset)

    finally:
        await rest_kraken.close()


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])