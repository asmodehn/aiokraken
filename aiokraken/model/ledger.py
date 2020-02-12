from __future__ import annotations

# https://www.kraken.com/features/websocket-api#message-ohlc
import dataclasses
from collections import namedtuple

import typing
from decimal import Decimal

from aiokraken.rest.schemas.kledger import KLedgerInfo

""" A common data structure for OHLC based on pandas """
from datetime import datetime, timezone

import pandas as pd
# CAREFUL to what we are doing
pd.set_option('mode.chained_assignment','raise')
# import pandas_ta as ta
import janitor


from aiokraken.utils.timeindexeddataframe import TimeindexedDataframe


class Ledger(TimeindexedDataframe):

    def __init__(self, ledger_as_dict: typing.Dict[str, KLedgerInfo], attr_index="time"):
        # Note we drop the key (should already be replicated in the value)
        df = pd.DataFrame.from_records(data=[dataclasses.asdict(v) for v in ledger_as_dict.values()], index=attr_index)

        df.index = pd.to_datetime(df.index, unit='s', utc=True)

        super(Ledger, self).__init__(data=df)
