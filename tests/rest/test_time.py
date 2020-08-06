import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient
from aiokraken.rest.schemas.time import Time


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_time(keyfile):
    """ get kraken trade balance"""
    async with RestClient(server=Server(**keyfile)) as rest_kraken:
        time= await rest_kraken.time()
        assert isinstance(time, Time)

        # Note : cassette recorded at 11:07 Paris Time
        # CAREFUL : this depends on locale (see rest.schemas.tests.test_time)
        # assert repr(time) == "2020-01-01T10:07:20+00:00"
        # assert str(time) == "Wed Jan  1 10:07:20 2020 UTC"
        assert time.unixtime == 1577873240
        print(time)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=all']) #new_episodes'])
