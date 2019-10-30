import pytest

from aiokraken.rest.schemas import PairModel, KCurrency
from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.model.ohlc import OHLC


# TODO : test multiple pairs... multiple ways...

@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc_pairmodel():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.ohlc(pair=PairModel(base=KCurrency.XBT, quote=KCurrency.EUR))
        print(f'response is \n{response.head()}')

        assert isinstance(response, OHLC)

    finally:
        await rest_kraken.close()


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc_pair_newstr():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.ohlc(pair="XBTEUR")
        print(f'response is \n{response.head()}')

        assert isinstance(response, OHLC)

    finally:
        await rest_kraken.close()


@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_ohlc_pair_oldstr():
    """ get kraken ohlc"""
    rest_kraken = RestClient(server=Server())
    try:
        response = await rest_kraken.ohlc(pair="XXBTZEUR")
        print(f'response is \n{response.head()}')

        assert isinstance(response, OHLC)

    finally:
        await rest_kraken.close()


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])