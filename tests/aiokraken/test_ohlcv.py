from decimal import Decimal

import pytest

from aiokraken.domain.assetpairs import AssetPairs
from aiokraken.domain.ohlcv import OHLCV
from aiokraken.model.ohlc import OHLC
from aiokraken.rest import RestClient, Server


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlcv_one_day():
    """ get aiokraken ohlcv"""
    server = Server()
    client = RestClient(server=server)

    mypairs = await AssetPairs.retrieve(pairs=["XBT/EUR", "XTZ/XBT", "ETH/CAD"], rest=client)
    ohlcv = await OHLCV.one_day(pairs=mypairs, rest=client)

    assert isinstance(ohlcv, OHLCV)

    subohlcv = ohlcv[["XBT/EUR", "XTZ/XBT"]]
    assert isinstance(subohlcv, OHLCV)
    assert "ETH/CAD" not in subohlcv

    xbt_eur = subohlcv["XBT/EUR"]
    assert isinstance(xbt_eur, OHLC)

    # TODO : more tests about time mapping


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--record-mode=new_episodes'])
