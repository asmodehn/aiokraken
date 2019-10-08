import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.ohlc import OHLC


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.ohlc(pair='XBTEUR')
        print(f'response is \n{response.head()}')

        assert isinstance(response, OHLC)

    finally:
        await rest_kraken.close()


if __name__ == '__main__':
    pytest.main(['-s', __file__])
