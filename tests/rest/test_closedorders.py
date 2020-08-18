from decimal import Decimal

import pytest

from aiokraken.rest.api import Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.krequestorder import RequestOrder


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_closedorders_nonempty(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        closedorders, count = await rest_kraken.closedorders()
        print(f'response is {closedorders}')

    # from cassette
    assert count == 2
    assert 'OEES77-MGNR7-HDQLW7' in closedorders
    assert 'OSFLKN-U4LLK-RVLQI4' in closedorders


if __name__ == '__main__':
    # replay
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
