import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.trade_balance import TradeBalance, TradeBalanceSchema


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_trade_balance(keyfile):
    """ get kraken trade balance"""
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        tradebalance = await rest_kraken.trade_balance()
        assert isinstance(tradebalance, TradeBalance)
        print(tradebalance)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=all']) #new_episodes'])
