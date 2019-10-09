# content of conftest.py
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--with-keyfile", action="store_true", default=False, help="run tests with private key"
    )


@pytest.fixture
def keyfile(request):
    kf = request.config.getoption("--with-keyfile")
    keystruct = None
    if kf:
        from aiokraken.config import load_api_keyfile
        keystruct = load_api_keyfile()
    return keystruct