import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.balance import Balance, BalanceSchema


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_balance(keyfile):
    """ get kraken balance"""
    async with RestClient(server=Server()) as rest_kraken:
        balance_run= rest_kraken.balance()
        response = await balance_run()
        assert isinstance(response, Balance)
        print(response)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
