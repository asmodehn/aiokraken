import pytest
from aiokraken.assets import Assets

@pytest.mark.asyncio
@pytest.mark.vcr()
async def test_assets():
    """ get aiokraken assets"""
    assets = Assets()
    await assets()  # Optional from the moment we have Local storage

    # TODO : more tests
    assert len(assets) == 41


if __name__ == '__main__':
    pytest.main(['-s', __file__, '--block-network'])
    # record run
    #pytest.main(['-s', __file__, '--with-keyfile', '--record-mode=new_episodes'])


