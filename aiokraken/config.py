import logging

import configparser

import os

# Resolve userpath to an absolute path
DEFAULT_KRAKEN_API_KEYFILE = os.path.expanduser('~/.config/aiokraken/kraken.key')

# If the environment variable is set, override the default value
KRAKEN_API_KEYFILE = os.getenv('AIOKRAKEN_API_KEYFILE', DEFAULT_KRAKEN_API_KEYFILE)
KRAKEN_API_KEYFILE = os.path.normpath(KRAKEN_API_KEYFILE)

logger = logging.getLogger('aiokraken.config')


def load_api_keyfile():
    """Load the Kraken API keyfile"""

    if not os.path.exists(KRAKEN_API_KEYFILE):
        logger.warning("The API keyfile {} was not found!".format(KRAKEN_API_KEYFILE))

    else:
        f = open(KRAKEN_API_KEYFILE, encoding="utf-8").readlines()
        return { 'key': f[0].strip(), 'secret': f[1].strip()}


if __name__ == '__main__':
    print(f"Keyfile: {KRAKEN_API_KEYFILE}")
    f = load_api_keyfile()
    print(f"KEY : {f.get('key')}")
    print(f"SECRET : {f.get('secret')}")

