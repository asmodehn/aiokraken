from decimal import Decimal

import pytest

from aiokraken.rest.api import Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.krequestorder import RequestOrder


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_ledgers_nonempty(keyfile):
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        ledgers, count = await rest_kraken.ledgers()
        while len(ledgers) < count:
            more_ledgers, count = await rest_kraken.ledgers(offset=len(ledgers))
            ledgers.update(more_ledgers)

        print(f'response is {ledgers}')

    # from cassette
    assert count == 13
    assert "L2OEFI-7UMQC-CQBLTV" in ledgers
    assert "LROUT5-5B3VT-V5FLTS" in ledgers
    assert "LF5JHR-DPMZL-M6XVFZ" in ledgers
    assert "LDOUZM-LD6P5-LXNEMX" in ledgers
    assert "LJSU5P-5ASDX-UF7GFH" in ledgers
    assert "L2QEFI-7UMQC-CQBLTV" in ledgers
    assert "LROUT5-5B3VT-V5FLTZ" in ledgers
    assert "LF5JWR-DPMZL-M6XVFZ" in ledgers
    assert "LDOUGM-LD6P5-LXNEMX" in ledgers
    assert "LJSE5P-5ASDX-UF7GFH" in ledgers
    assert "L2OEFI-7UMQC-CQCLTV" in ledgers
    assert "LROUT5-5B3VT-V5FLTO" in ledgers
    assert "LF5JBR-DPMZL-M6XVFA" in ledgers


if __name__ == '__main__':
    # replay
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
