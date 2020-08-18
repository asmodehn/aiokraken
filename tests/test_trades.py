from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from aiokraken.rest.schemas.ktrade import KTradeModel

from aiokraken.rest.schemas.kledger import KLedgerInfo

from aiokraken.trades import Trades

from aiokraken.rest import RestClient, Server


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_trades(keyfile):
    """ get aiokraken trades"""
    server = Server(key=keyfile.get('key'), secret=keyfile.get('secret'))
    client = RestClient(server=server)

    start_test = datetime(year=2019, month=11, day=4, hour=17, minute=25, tzinfo=timezone.utc)
    end_test = datetime.fromisoformat("2020-04-29 14:00:00+00:00")
    # Note : pytest-recording doesnt seem to care about timestamps to match...
    history = await Trades.retrieve(start=start_test, end=end_test, rest=client)

    assert isinstance(history, Trades)

    subhistory = history[datetime.fromisoformat("2020-07-11 17:00:00+00:00"):datetime.fromisoformat("2020-08-23 06:40:00+00:00")]
    assert isinstance(subhistory, Trades)
    assert len(subhistory) == 5
    assert datetime.fromisoformat("2020-08-23 07:26:18+00:00") not in subhistory

    dtldg = subhistory[datetime.fromisoformat("2020-08-23 06:38:46+00:00")]
    assert isinstance(dtldg, KTradeModel)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
