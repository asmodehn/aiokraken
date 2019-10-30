import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.ticker import Ticker


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ticker():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.ticker(pairs=['XBTEUR'])
        print(f'response is \n{response}')

        assert isinstance(response, Ticker)

    finally:
        await rest_kraken.close()


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
