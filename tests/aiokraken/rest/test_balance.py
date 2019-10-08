import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
#from aiokraken.model. import OHLC


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_balance():
    """ get kraken balance"""

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:
        response = await rest_kraken.balance()
        await rest_kraken.close()
        print(f'response is {response}')

        # TODO : assert smthg ?

    finally:
        await rest_kraken.close()


if __name__ == '__main__':
    pytest.main(['-s', __file__])
