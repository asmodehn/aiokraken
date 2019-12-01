import logging

import configparser

import os
import tinydb
#import sqlite3

# Resolve userpath to an absolute path
from tinydb import TinyDB

DEFAULT_KRAKEN_API_KEYFILE = os.path.expanduser('~/.config/aiokraken/kraken.key')
DEFAULT_KRAKEN_PERSIST = os.path.expanduser('~/.config/aiokraken/kraken.json')
#DEFAULT_KRAKEN_DB_FILE = os.path.expanduser('~/.config/aiokraken/kraken.db')

# If the environment variable is set, override the default value
KRAKEN_API_KEYFILE = os.getenv('AIOKRAKEN_API_KEYFILE', DEFAULT_KRAKEN_API_KEYFILE)
KRAKEN_API_KEYFILE = os.path.normpath(KRAKEN_API_KEYFILE)

KRAKEN_PERSIST_FILE = os.getenv('AIOKRAKEN_PERSIST', DEFAULT_KRAKEN_PERSIST)
KRAKEN_PERSIST_FILE = os.path.normpath(KRAKEN_PERSIST_FILE)

# KRAKEN_DB_FILE = os.getenv('AIOKRAKEN_DB_FILE', DEFAULT_KRAKEN_DB_FILE)
# KRAKEN_DB_FILE = os.path.normpath(KRAKEN_DB_FILE)

logger = logging.getLogger('aiokraken.config')


def load_api_keyfile():
    """Load the Kraken API keyfile"""

    if not os.path.exists(KRAKEN_API_KEYFILE):
        logger.warning("The API keyfile {} was not found!".format(KRAKEN_API_KEYFILE))

    else:
        f = open(KRAKEN_API_KEYFILE, encoding="utf-8").readlines()
        return {'key': f[0].strip(), 'secret': f[1].strip()}


def load_persist():
    """Load persistance layer"""

    db = TinyDB(KRAKEN_PERSIST_FILE)

    return {db.table(t).name: db.table(t) for t in db.tables()}


# def connect_db():
#     """ Load the Kraken DB file"""
#
#     if not os.path.exists(KRAKEN_DB_FILE):
#         logger.warning("The DB file {} was not found!". format(KRAKEN_DB_FILE))
#
#     else:
#         c = sqlite3.connect(KRAKEN_DB_FILE)
#         return c


if __name__ == '__main__':
    print(f"Keyfile: {KRAKEN_API_KEYFILE}")
    f = load_api_keyfile()
    print(f"KEY : {f.get('key')}")
    print(f"SECRET : {f.get('secret')}")

    print(f"Persistence: {KRAKEN_PERSIST_FILE}")
    f = load_persist()
    print(f"Tables: {f.get('assets')}")

    # print(f"DBfile: {KRAKEN_DB_FILE}")
    # c = connect_db()
    # cursor = c.cursor()
    # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # print(cursor.fetchall())
