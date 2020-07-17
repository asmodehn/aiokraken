import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.ohlc import OHLC


# TODO : test multiple pairs... multiple ways...


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc_pair_newstr():
    """ get kraken ohlc"""
    async with RestClient(server=Server()) as rest_kraken:
        ohlc = await rest_kraken.ohlc(pair="XBTEUR")
        print(f'response is \n{ohlc.head()}')

        assert isinstance(ohlc, OHLC)

@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc_pair_oldstr():
    """ get kraken ohlc"""
    async with RestClient(server=Server()) as rest_kraken:
        ohlc= await rest_kraken.ohlc(pair="XXBTZEUR")
        print(f'response is \n{ohlc.head()}')

        assert isinstance(ohlc, OHLC)


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc_pair_propertype():
    """ get kraken ohlc"""
    async with RestClient(server=Server()) as rest_kraken:
        assetpairs = await rest_kraken.retrieve_assetpairs()
        ohlc = await rest_kraken.ohlc(pair=assetpairs["XXBTZEUR"])
        print(f'response is \n{ohlc.head()}')

        assert isinstance(ohlc, OHLC)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])