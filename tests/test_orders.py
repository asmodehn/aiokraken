from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from aiokraken.orders import Orders
from aiokraken.rest.schemas.kopenorder import KOpenOrderModel

from aiokraken.rest import RestClient, Server


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_orders(keyfile):
    """ get aiokraken orders"""
    server = Server(key=keyfile.get('key'), secret=keyfile.get('secret'))
    client = RestClient(server=server)

    start_test = datetime(year=2019, month=11, day=4, hour=17, minute=25, tzinfo=timezone.utc)
    end_test = datetime.fromisoformat("2020-04-29 14:00:00+00:00")
    # Note : pytest-recording doesnt seem to care about timestamps to match...
    orders = await Orders.retrieve(start=start_test, end=end_test, rest=client)

    assert isinstance(orders, Orders)

    subhistory = orders[datetime.fromisoformat("2020-07-11 17:00:00+00:00"):datetime.fromisoformat("2020-08-23 06:40:00+00:00")]
    assert isinstance(subhistory, Orders)
    assert len(subhistory) == 5
    assert datetime.fromisoformat("2020-08-23 07:26:18+00:00") not in subhistory

    dtldg = subhistory[datetime.fromisoformat("2020-08-23 06:38:46+00:00")]
    assert isinstance(dtldg, KOpenOrderModel)

if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
