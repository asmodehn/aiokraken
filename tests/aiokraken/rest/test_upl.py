import pytest

from aiokraken.rest.upl import Kraken
from aiokraken.model.time import Time


@pytest.mark.vcr()
def test_time():
    response = Kraken(base_url="https://api.kraken.com/").get_time()
    print(response)
    assert isinstance(response, Time)


if __name__ == '__main__':
    pytest.main(['-s', __file__])
