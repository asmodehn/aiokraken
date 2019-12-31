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
        ohlc_run = rest_kraken.ohlc(pair="XBTEUR")
        response = await ohlc_run()
        print(f'response is \n{response.head()}')

        assert isinstance(response, OHLC)

@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc_pair_oldstr():
    """ get kraken ohlc"""
    async with RestClient(server=Server()) as rest_kraken:
        ohlc_run = rest_kraken.ohlc(pair="XXBTZEUR")
        response = await ohlc_run()
        print(f'response is \n{response.head()}')

        assert isinstance(response, OHLC)



if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])