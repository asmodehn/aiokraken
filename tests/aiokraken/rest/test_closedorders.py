from decimal import Decimal

import pytest

from aiokraken.rest.api import Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.krequestorder import RequestOrder


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_closedorders_nonempty(keyfile):
    async with RestClient(server=Server()) as rest_kraken:
        closedorders_run = rest_kraken.closedorders()
        response = await closedorders_run()
    print(f'response is {response}')

    assert response == {}

if __name__ == '__main__':
    # replay
    #pytest.main(['-s', __file__, '--block-network'])
    # record run
    pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
