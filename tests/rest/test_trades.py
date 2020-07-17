from decimal import Decimal

import pytest

from aiokraken.rest.api import Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.krequestorder import RequestOrder


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_trades_nonempty(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        trades, count = await rest_kraken.trades(offset=0)
        print(f'response is {trades}')

        # from cassette
        assert count == 12
        assert 'TWSFUZ-YBBCM-XFU2FG' in trades
        assert 'TJFV3P-TGSJ4-TCAEUD' in trades
        assert 'T7IONT-NOOLP-5X3PGX' in trades
        assert 'T2SXUI-QWKSI-HFJIT6' in trades
        assert 'TYMPWS-43QSS-5YWAGD' in trades
        assert 'T5UIUL-2SZBI-VIOGIG' in trades
        assert 'T2WW7B-CAW77-BDXKIR' in trades
        assert 'TNDNSP-4H6HR-GL5NWP' in trades
        assert 'TXIRKD-TWZVQ-ZYPQRH' in trades
        assert 'TQIWNZ-GOXOH-VLRDCE' in trades
        assert 'TZT4H6-MKFDM-DAVW4C' in trades
        assert 'THNILV-B4KOW-NCBBTN' in trades

if __name__ == '__main__':
    # replay
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
