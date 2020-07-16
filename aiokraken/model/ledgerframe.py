from __future__ import annotations

# https://www.kraken.com/features/websocket-api#message-ohlc
import dataclasses
from collections import namedtuple

import typing
from decimal import Decimal

from pandas import DatetimeIndex

from aiokraken.model.asset import Asset
from result import Result, Ok

from aiokraken.rest.schemas.kledger import KLedgerInfo

""" A common data structure for ledger based on pandas """
from datetime import datetime, timezone

import pandas as pd
# CAREFUL to what we are doing
pd.set_option('mode.chained_assignment', 'raise')
# import pandas_ta as ta
import janitor


# TODO : investigate pandas potential replacement for immutable data :
#  https://github.com/InvestmentSystems/static-frame

from aiokraken.utils.timeindexeddataframe import TimeindexedDataframe


class LedgerFrame(TimeindexedDataframe):

    def __init__(self, dataframe: pd.DataFrame, assets = None):
        # TODO : maybe some of this should move into parent class ?
        # drop duplicates : this is a set, there should not be any duplicates (ids are included)
        if dataframe.duplicated().any():
            print("DUPLICATES FOUND ! SHOULD NOT HAPPEN.. DROPPING")
            dataframe.drop_duplicates(inplace=True)

        if not isinstance(dataframe.index, DatetimeIndex):
            # TODO : FIX: A value is trying to be set on a copy of a slice from a DataFrame.
            dataframe["datetime"] = pd.to_datetime(dataframe.time, unit='s', utc=True, origin='unix', errors='raise')
            # switching index to the converted timestamp
            dataframe.set_index("datetime", drop=True, inplace=True)
            dataframe.sort_index(axis=0, inplace=True)
        super(LedgerFrame, self).__init__(data=dataframe)

        self.assets = assets  # the list of assets we track in this ledger frame. None means "all".

    def __repr__(self):
        # TODO : HOWTO do this ?
        return repr(self.dataframe)

    def stitch(self, l: LedgerFrame) -> LedgerFrame:

        # merging without considereing indexes
        newdf_noidx = self.dataframe.reset_index().merge(l.dataframe.reset_index(), how='outer')

        # dropping duplicates (TODO : better/cleaner merge ?)
        newdf = newdf_noidx.drop_duplicates()

        # building new tradehistory (should take care of times and indexing properly)
        new_th = LedgerFrame(dataframe=newdf.copy())  # explicit copy to prevent modifying self.

        # REMINDER : immutability interface design.
        return new_th

    # # TODO : one property per type for filtering
    # @property
    # def thing(self):
    #     return
    #
    def __getitem__(self, item: typing.Union[Asset, typing.List[Asset]]):
        """ Access by asset only (mapping with datetime keys should be done elsewhere, ie. one layer up)."""

        if isinstance(item, Asset):
            return LedgerFrame(
                dataframe = self.dataframe.loc[self.dataframe['asset'] == item.restname],
                assets=item)
        elif isinstance(item, list):
            return LedgerFrame(
                dataframe = self.dataframe.loc[self.dataframe['asset'].isin(i.restname for i in item)],
                assets=item)
        elif isinstance(item, slice):
            return LedgerFrame(
                dataframe = self.dataframe[item],  # let dataframe manage time slices
                assets=self.assets)
        elif isinstance(item, (datetime, str)):
            # use usual access via key/index, as for a mapping over time...
            return KLedgerInfo(**self.dataframe.loc[item])
        else:
            raise KeyError(f"{item} not found")

        # TODO polish : note the mapping here is along the item line (not the time like for OHLC !)

        #
        # if isinstance(item, slice):
        #     # slice returns another instance with the slice as dataframe
        #     return LedgerFrame(dataframe=self.dataframe[item].copy())
        # elif isinstance(item, int):  # Note : because of this, access by timestamp (int) directly cannot work.
        #     return self.dataframe.iloc[item]
        # else:
        #     return self.dataframe.loc[item]

    def __len__(self):
        return len(self.dataframe)


def ledgerframe(ledger_as_dict: typing.Dict[str, KLedgerInfo]) -> Result[LedgerFrame]:
    if not ledger_as_dict:
        df = pd.DataFrame(columns=[f.name for f in dataclasses.fields(KLedgerInfo)])  # we only know about index name
    else:
        # Note we drop the key (should already be replicated in the value)
        df = pd.DataFrame.from_records(data=[dataclasses.asdict(v) for v in ledger_as_dict.values()])

    return Ok(LedgerFrame(dataframe=df))
