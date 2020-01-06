import pytest


# Here we load everything from main without launching the cli
from aiokraken import __main__
# now we can test cli behavior from python directly , via click

@pytest.mark.runner_setup(charset='cp1251', env={'test': 1}, echo_stdin=True)
def test_runner_setup(cli_runner):

    # result = cli_runner.invoke(hello, ['Peter'])
    # assert result.exit_code == 0
    # assert result.output == 'Hello Peter!\n'

    pass

# TODO : find how to simulate filesystem in test to validate config behavior...







