from decimal import Decimal

import pytest
from aiokraken.domain.assets import Assets
from aiokraken.rest import RestClient, Server


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assets():
    """ get aiokraken assets"""
    assets = await Assets.retrieve()

    # TODO : more tests
    assert len(assets) == 48


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_assets_balance(keyfile):
    """ get aiokraken assets"""
    server = Server(key=keyfile.get('key'), secret=keyfile.get('secret'))
    client = RestClient(server=server)

    assets = await Assets.retrieve(rest=client)
    b = await assets.balance(rest=client)

    assert b["ZEUR"] == Decimal("83.1177")
    assert b["XXBT"] == Decimal("0.0251625000")
    assert b["XXRP"] == 0
    assert b["XETH"] == 0
    assert b["XETC"] == 50
    assert b["EOS"] == 50
    assert b["BCH"] == Decimal("1.8921568")
    assert b["ADA"] == 55
    assert b["XTZ"] == Decimal("0.00000005")
    assert b["BSV"] == 0
    

if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])


