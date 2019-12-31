import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.ticker import Ticker


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ticker_one():
    """ get kraken ticker"""
    async with RestClient(server=Server()) as rest_kraken:
        ticker_run = rest_kraken.ticker(pairs=['XBTEUR'])
        response = await ticker_run()
        print(f'response is \n{response}')
        assert len(response) == 1
        pm = "XXBTZEUR"  # TODO : handle conversion problem...
        assert pm in response
        assert isinstance(response.get(pm), Ticker)


# TODO : multiple ticker request test...

if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
