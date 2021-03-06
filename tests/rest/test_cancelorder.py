from decimal import Decimal

import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.krequestorder import RequestOrder

# vcr configuration ? : https://github.com/kiwicom/pytest-recording#configuration
# AddOrder (validate false)
# get OrderID
# CAncelOrder
# see : https://support.kraken.com/hc/en-us/articles/360000919926-Does-Kraken-offer-a-Test-API-or-Sandbox-Mode-


#@pytest.mark.dependency(depends=["test_add_sell_limit_order_validate"])
@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_cancel_limit_order_id_execute(keyfile):
    async with RestClient(server=Server()) as rest_kraken:
        ticker = await rest_kraken.ticker(pairs=['XXBTZEUR'])
        tickerresponse = ticker.get("XXBTZEUR")
        assert tickerresponse
        print(tickerresponse)
        # computing realistic price, but unlikely to be filled, even after relative_starttm delay.
        # and even if it is filled it s probably a good thing ;)
        # Ref : https://support.kraken.com/hc/en-us/articles/360000919926-Does-Kraken-offer-a-Test-API-or-Sandbox-Mode-
        high_price = tickerresponse.ask.price * Decimal(1.5)
        # delayed market order
        bidresponse = await rest_kraken.addorder(order=RequestOrder(
            pair="XBTEUR",
        ).limit(limit_price=high_price).ask(
            volume='0.01',).delay(
            relative_expiretm=15,  # expire in 15 seconds (better than cancelling since cancelling too often can lock us out)
        ).execute(True))
        # TODO : verify balance before, this will trigger error if not enough funds.
        assert bidresponse
        print(bidresponse)
        # todo : get order ID
        # TODO : Check visible in openorders

        openorders = rest_kraken.openorders()
        assert openorders
        print(f'response is {openorders}')

        # TODO : cancel it with orderid
        # TODO : check not visible in openorders



# AddOrder with userref (validate false)
# CancelOrder with userref
# see : https://www.kraken.com/features/api#cancel-open-order


#@pytest.mark.dependency(depends=["test_add_sell_limit_order_validate"])
@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_cancel_limit_order_userref_execute(keyfile):
    async with RestClient(server=Server()) as rest_kraken:
        ticker = await rest_kraken.ticker(pairs=['XXBTZEUR'])
        tickerresponse = ticker.get("XXBTZEUR")
        assert tickerresponse
        print(tickerresponse)
        # computing realistic price, but unlikely to be filled, even after relative_starttm delay.
        # and even if it is filled it s probably a good thing ;)
        # Ref : https://support.kraken.com/hc/en-us/articles/360000919926-Does-Kraken-offer-a-Test-API-or-Sandbox-Mode-
        high_price = tickerresponse.ask.price * Decimal(1.5)
        # delayed market order
        bidresponse = await rest_kraken.addorder(order=RequestOrder(
            pair="XBTEUR",
        ).limit(
            limit_price=high_price,).ask(
            volume='0.01',).delay(
            relative_expiretm=15,  # expire in 15 seconds (better than cancelling since cancelling too often can lock us out)
        ).execute(
            execute=True,))
        # TODO : verify balance before, this will trigger error if not enough funds.
        assert bidresponse
        print(bidresponse)

        # TODO : Check visible in openorders via userref

        openorders = await rest_kraken.openorders()
        assert openorders
        print(f'response is {openorders}')

        # TODO : cancel it with userref
        # TODO : check not visible in openorders


if __name__ == '__main__':
    # replay run
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
