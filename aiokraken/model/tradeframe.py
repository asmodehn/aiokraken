from __future__ import annotations

# https://www.kraken.com/features/websocket-api#message-ohlc
import dataclasses
from collections import namedtuple

import typing
from decimal import Decimal

from pandas._libs.tslibs.np_datetime import OutOfBoundsDatetime
from result import Result, Ok

from aiokraken.rest.schemas.ktrade import KTradeModel

""" A common data structure for trades based on pandas """
from datetime import datetime, timezone

import pandas as pd
# CAREFUL to what we are doing
pd.set_option('mode.chained_assignment', 'raise')
import janitor


from aiokraken.utils.timeindexeddataframe import TimeindexedDataframe


class TradeFrame(TimeindexedDataframe):

    def __init__(self, dataframe: pd.DataFrame):
        # TODO : maybe some of this should move into parent class ?
        # drop duplicates : this is a set, there should not be any duplicates (ids are included)
        if dataframe.duplicated().any():
            print("DUPLICATES FOUND ! SHOULD NOT HAPPEN.. DROPPING")
            dataframe.drop_duplicates(inplace=True)
        #TODO : enforce dtypes of dataframe from original object model...
        dataframe["datetime"] = pd.to_datetime(dataframe.time, unit='s', utc=True, origin='unix', errors='raise')
        # switching index to the converted timestamp
        dataframe.set_index("datetime", drop=True, inplace=True)
        dataframe.sort_index(axis = 0, inplace=True)
        super(TradeFrame, self).__init__(data=dataframe)

    def __repr__(self):
        # TODO : HOWTO do this ?
        return repr(self.dataframe)

    def stitch(self, th: TradeFrame) -> TradeFrame:

        # merging without considereing indexes
        newdf_noidx = self.dataframe.reset_index().merge(th.dataframe.reset_index(), how='outer')

        # dropping duplicates (TODO : better/cleaner merge ?)
        newdf = newdf_noidx.drop_duplicates()

        # building new tradehistory (should take care of times and indexing properly)
        new_th = TradeFrame(dataframe=newdf.copy())  # explicit copy to prevent modifying self.

        # REMINDER : immutability interface design.
        return new_th

    # # TODO : one property per type for filtering
    # @property
    # def thing(self):
    #     return
    #
    def __getitem__(self, item):
        """ Access by (date)times only (mapping interface should be done elsewhere, ie. one layer up)."""
        if isinstance(item, slice):
            # slice returns another instance with the slice as dataframe
            return TradeFrame(dataframe=self.dataframe[item].copy())
        elif isinstance(item, int):  # Note : because of this, access by timestamp (int) directly cannot work.
            return self.dataframe.iloc[item]
        else:
            return self.dataframe.loc[item]

    def __len__(self):
        return len(self.dataframe)


def tradeframe(tradehistory_as_dict: typing.Dict[str, KTradeModel]) -> Result[TradeFrame]:
    if not tradehistory_as_dict:
        df = pd.DataFrame(columns=[f.name for f in dataclasses.fields(KTradeModel)])  # we only know about index name
    else:
        # Note we drop the key (should already be replicated in the value)
        df = pd.DataFrame.from_records(data=[dataclasses.asdict(v) for v in tradehistory_as_dict.values()])

    return Ok(TradeFrame(dataframe=df))


if __name__ == '__main__':
    pass  # EXAMPLE TODO
