import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.balance import Balance, BalanceSchema


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_balance(keyfile):
    """ get kraken balance"""
    server = Server(key = keyfile.get('key'), secret = keyfile.get('secret'))
    async with RestClient(server=server) as rest_kraken:
        balance = await rest_kraken.balance()
        assert isinstance(balance, dict)  # TODO : proper type here
        print(balance)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
