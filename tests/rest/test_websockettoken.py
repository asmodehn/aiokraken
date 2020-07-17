import pytest

from aiokraken.rest.api import API, Server
from aiokraken.rest.client import RestClient


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=['API-Key', 'API-Sign'])
async def test_websocket(keyfile):
    """ get kraken websocket token"""
    server = Server(key = keyfile.get('key'), secret = keyfile.get('secret'))
    async with RestClient(server=server) as rest_kraken:
        token = await rest_kraken.websockets_token()
        assert isinstance(token, str)  # TODO : proper type here
        print(token)


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    # pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])
