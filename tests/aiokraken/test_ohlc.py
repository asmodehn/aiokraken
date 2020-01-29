import time

import pytest
from aiokraken.model.timeframe import KTimeFrameModel

from aiokraken.ohlc import OHLC

@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc():
    """ get aiokraken ohlc"""

    # ohlc data can be global (one per market*timeframe only)
    ohlc = OHLC(pair='ETHEUR', timeframe=KTimeFrameModel.one_minute)

    assert len(ohlc) == 0

    await ohlc()

    print(f"from: {ohlc.impl.begin} to: {ohlc.impl.end} -> {len(ohlc)} values")
    assert len(ohlc) == 720

    M = 1
    print(f"Waiting {M} more minutes to attempt retrieving more ohlc data and stitch them...")

    time.sleep(M * 60)  # only when recording

    await ohlc()

    print( f"from: {ohlc.impl.begin} to: {ohlc.impl.end} -> {len(ohlc)} values")
    assert len(ohlc) == 720 + M

    # TODO : more tests


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # we need to record "all" here to make sure we record multiple calls to the same url
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=all'])


