from decimal import Decimal

import pytest

from aiokraken.rest.api import Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.krequestorder import RequestOrder


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_openorders_empty(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        openorders = await rest_kraken.openorders()
    print(f'response is {openorders}')

    assert openorders == {}


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_openorders_one_high_limit_sell(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        ticker = await rest_kraken.ticker(pairs=['XXBTZEUR'])
        tickerresponse = ticker.get("XXBTZEUR")  # TODO : handle conversion problem...
        assert tickerresponse
        print(tickerresponse)
        # pass high limit sell order
        ask_high_price = tickerresponse.ask.price * Decimal(1.5)
        askresponse = await rest_kraken.addorder(order=RequestOrder(
            pair="XBTEUR"
        ).limit(
            limit_price=ask_high_price,)
        .ask(
            volume='0.01',)
        .delay(
            relative_expiretm=15,)
        .execute(True))
        assert askresponse
        print(askresponse)

        # get open orders to make sure we can find it
        openorders = await rest_kraken.openorders()
        print(f'response is {openorders}')

    assert openorders


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_openorders_one_low_limit_buy(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        ticker = await rest_kraken.ticker(pairs=['XXBTZEUR'])
        tickerresponse = ticker.get("XXBTZEUR")  # TODO : handle conversion problem...
        assert tickerresponse
        print(tickerresponse)
        # computing realistic price, but unlikely to be filled, even after relative_starttm delay.
        low_price = tickerresponse.bid.price * Decimal(0.5)
        # delayed market order
        bidresponse = await rest_kraken.addorder(order=RequestOrder(
            pair="XBTEUR"
        ).limit(
            limit_price=low_price,)
        .bid(
            volume='0.01',)
        .delay(
            relative_expiretm=15,)
        .execute(True))
        assert bidresponse
        print(bidresponse)

        openorders = await rest_kraken.openorders()
        assert openorders
        print(f'response is {openorders}')


if __name__ == '__main__':
    # replay
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
