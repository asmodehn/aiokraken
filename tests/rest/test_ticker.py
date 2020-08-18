import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.ticker import Ticker


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ticker_one_str():
    """ get kraken ticker"""
    async with RestClient(server=Server()) as rest_kraken:
        ticker = await rest_kraken.ticker(pairs=['XXBTZEUR'])
        print(f'response is \n{ticker}')
        assert len(ticker) == 1
        assert "XXBTZEUR" in ticker
        assert isinstance(ticker.get("XXBTZEUR"), Ticker)


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ticker_one_pair():
    """ get kraken ticker"""
    async with RestClient(server=Server()) as rest_kraken:
        assetpairs = await rest_kraken.retrieve_assetpairs()
        ticker = await rest_kraken.ticker(pairs=[assetpairs["XXBTZEUR"]])
        print(f'response is \n{ticker}')
        assert len(ticker) == 1
        assert "XXBTZEUR" in ticker
        assert isinstance(ticker.get("XXBTZEUR"), Ticker)

# TODO : multiple ticker request test...


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
