import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.ticker import Ticker


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ticker_one():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:

        response = await rest_kraken.ticker(pairs=['XBTEUR'])
        print(f'response is \n{response}')
        assert len(response) == 1
        pm = "XXBTZEUR"  # TODO : handle conversion problem...
        assert pm in response
        assert isinstance(response.get(pm), Ticker)

    finally:
        await rest_kraken.close()


# TODO : multiple ticker request test...

if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
