import re
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from aiokraken.model.assetpair import AssetPair

from aiokraken.ohlcv import OHLCV
from aiokraken.model.ohlc import OHLC

from aiokraken.model.ticker import Ticker

from aiokraken.assetpairs import AssetPairs
from aiokraken.rest import RestClient, Server


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs():
    """ get aiokraken assetpairs"""
    assetpairs = await AssetPairs.retrieve()

    # Retrieve ALL pairs (except dark pools)
    assert len(assetpairs) == 168

    # check we get proper pair type when iterating (implicitly correct by iterating on values)
    for p in assetpairs:
        assert isinstance(p, AssetPair)

    for pv in assetpairs.values():
        assert isinstance(pv, AssetPair)

    # check we have proper consistent names in keys when iterating (unicity in keys)
    # base_quote = re.compile("[A-Z]*/[A-Z]*(.d)?")
    base_quote = re.compile("[A-Z]*/[A-Z]*")  # No dark pools here
    for p in assetpairs.keys():
        assert p is not None
        assert base_quote.match(p), f"{p} doesn't match {base_quote.pattern}"

    # checking items() behaves as expected
    for ps, pv  in assetpairs.items():
        assert isinstance(pv, AssetPair) and ps == pv.wsname
        assert isinstance(ps, str) and base_quote.match(ps)

    # check we have all possible names when calling __contains__
    assert "XETHZCAD" in assetpairs
    assert "XTZ/XBT" in assetpairs
    # TODO : more tests on known examples here...

    # check we can retrieve pairs even with all possible names
    assert isinstance(assetpairs["XETHZCAD"], AssetPair)
    assert isinstance(assetpairs["XTZ/XBT"], AssetPair)
    # TODO : more tests on known examples here...


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs_ticker():
    """ get aiokraken assets"""
    server = Server()
    client = RestClient(server=server)

    # getting a subset of pairs we are interested in
    assetpairs = await AssetPairs.retrieve(pairs=["XBT/EUR", "XTZ/XBT", "ETH/CAD"], rest=client)
    t = await assetpairs.ticker(rest=client)

    # TODO : maybe rename the keys to use the more consistent wsname...
    assert isinstance(t["ETH/CAD"], Ticker)
    assert isinstance(t["XTZ/XBT"], Ticker)
    assert isinstance(t["XBT/EUR"], Ticker)


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assetpairs_ohlcv():
    server = Server()
    client = RestClient(server=server)

    assetpairs = await AssetPairs.retrieve(pairs=["XBT/EUR", "XTZ/XBT", "ETH/CAD"], rest=client)
    now = datetime.now()
    o = await assetpairs.ohlcv(rest=client, start=now - timedelta(weeks=4), stop=now)

    assert isinstance(o["ETH/CAD"], OHLC)
    assert isinstance(o["XTZ/XBT"], OHLC)
    assert isinstance(o["XBT/EUR"], OHLC)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--record-mode=new_episodes'])


