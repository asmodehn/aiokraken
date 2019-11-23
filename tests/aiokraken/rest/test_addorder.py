from decimal import Decimal

import pytest

from aiokraken.rest.api import Server
from aiokraken.rest.client import RestClient

# vcr configuration ? : https://github.com/kiwicom/pytest-recording#configuration
from aiokraken.rest.schemas.krequestorder import RequestOrder


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_buy_market_order_validate(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        addorder_run = rest_kraken.addorder(order=RequestOrder(pair="XBTEUR", ).market().bid(volume='0.01'))
        response = await addorder_run()
        print(f'response is {response}')

        assert response


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_sell_market_order(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        addorder_run = rest_kraken.addorder(order=RequestOrder(pair="XBTEUR", ).market().ask(volume='0.01'))
        response = await addorder_run()

        print(f'response is {response}')

        assert response


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_buy_limit_order_validate(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        addorder_run = rest_kraken.addorder(order=RequestOrder(pair="XBTEUR", userref=54321).limit(limit_price=1234).bid(volume='0.01').delay(relative_starttm=60,))
        # CAREFUL here. Orders should be on 'validate' mode, but still it would be better to get current price asap... TODO
        response = await addorder_run()

        print(f'response is {response}')

        assert response


#@pytest.mark.dependency(depends=["test_add_buy_limit_order_validate"])
@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_buy_limit_order_execute_low(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        ticker_run = rest_kraken.ticker(pairs=['XBTEUR'])
        tickerresponse =(await ticker_run()).get("XXBTZEUR")  # TODO : handle conversion problem...
        assert tickerresponse
        print(tickerresponse)
        # computing realistic price, but unlikely to be filled, even after relative_starttm delay.
        # and even if it is filled it s probably a good thing ;)
        # Ref : https://support.kraken.com/hc/en-us/articles/360000919926-Does-Kraken-offer-a-Test-API-or-Sandbox-Mode-
        low_price = tickerresponse.bid.price * Decimal(0.5)
        # delayed market order
        addorder_run = rest_kraken.addorder(
            order=RequestOrder(pair="XBTEUR",  # userref=12345
        ).limit(limit_price=low_price,)
         .bid(volume='0.01',)
         .delay(relative_expiretm=15,)  # expire in 15 seconds (better than cancelling since cancelling too often can lock us out)
         .execute(True))
        bidresponse= await addorder_run()
        # TODO : verify balance before, this will trigger error if not enough funds.
        assert bidresponse
        print(bidresponse)



@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_sell_limit_order_validate(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        # CAREFUL here. Orders should be on 'validate' mode, but still it would be better to get current price asap... TODO
        addorder_run = rest_kraken.addorder(
            order=RequestOrder(pair="XBTEUR")
                .limit( limit_price=1234)
                .ask(volume='0.01')
                )
        response = await addorder_run()
        print(f'response is {response}')

        assert response


#@pytest.mark.dependency(depends=["test_add_sell_limit_order_validate"])
@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_sell_limit_order_execute_high(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        ticker_run = rest_kraken.ticker(pairs=['XBTEUR'])
        tickerresponse = (await ticker_run()).get("XXBTZEUR")
        assert tickerresponse
        print(tickerresponse)
        # computing realistic price, but unlikely to be filled, even after relative_starttm delay.
        # and even if it is filled it s probably a good thing ;)
        # Ref : https://support.kraken.com/hc/en-us/articles/360000919926-Does-Kraken-offer-a-Test-API-or-Sandbox-Mode-
        high_price = tickerresponse.ask.price * Decimal(1.5)
        # delayed market order
        addorder_run = rest_kraken.addorder(
            order=RequestOrder(pair="XBTEUR")
                .limit(limit_price=high_price,)
                .ask(volume='0.01',)
                .delay(relative_expiretm=15,) # expire in 15 seconds (better than cancelling since cancelling too often can lock us out)
                .execute(True))
        bidresponse = await addorder_run()
        # TODO : verify balance before, this will trigger error if not enough funds.
        assert bidresponse
        print(bidresponse)


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_buy_stop_order(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        # CAREFUL here. Orders should be on 'validate' mode, but still it would be better to get current price asap... TODO
        addorder_run = rest_kraken.addorder(
            order=RequestOrder(pair="XBTEUR")
                .stop_loss(stop_loss_price=1234)
                .bid( volume='0.01'))
        response = await addorder_run()
        print(f'response is {response}')

        assert response


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_add_sell_stop_order(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        # CAREFUL here. Orders should be on 'validate' mode, but still it would be better to get current price asap... TODO
        addorder_run = rest_kraken.addorder(
            order=RequestOrder(pair="XBTEUR")
                    .stop_loss(stop_loss_price=1234)
                    .ask(volume='0.01'))
        response = await addorder_run()
    print(f'response is {response}')

    assert response


if __name__ == '__main__':
    # replay run
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
