import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.order import MarketOrder, bid, ask


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_buy_order():
    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:
        response = await rest_kraken.bid(order=bid(MarketOrder(pair='XBTEUR', volume='0.01', )))
    finally:
        await rest_kraken.close()
    print(f'response is {response}')

    assert response


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_sell_order():

    from aiokraken.config import load_api_keyfile
    keystruct = load_api_keyfile()
    rest_kraken = RestClient(server=Server(key=keystruct.get('key'),
                                           secret=keystruct.get('secret')))
    try:
        response = await rest_kraken.ask(order=ask(MarketOrder(pair='XBTEUR', volume='0.01', )))
    finally:
        await rest_kraken.close()
    print(f'response is {response}')

    assert response


if __name__ == '__main__':
    pytest.main(['-s', __file__])
