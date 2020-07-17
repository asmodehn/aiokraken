from __future__ import annotations

# https://www.kraken.com/features/websocket-api#message-ohlc
import dataclasses
from collections import namedtuple

import typing
from decimal import Decimal

import pandas

from aiokraken.rest.schemas.kopenorder import KOpenOrderModel

from aiokraken.rest.schemas.kclosedorder import KClosedOrderModel
from pandas import DatetimeIndex

from aiokraken.model.assetpair import AssetPair

from aiokraken.model.asset import Asset
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


class OrderFrame(TimeindexedDataframe):

    def __init__(self, dataframe: pd.DataFrame, index="time", pairs = None):
        # TODO : maybe some of this should move into parent class ?
        # drop duplicates : this is a set, there should not be any duplicates (ids are included)
        if dataframe.duplicated().any():
            print("DUPLICATES FOUND ! SHOULD NOT HAPPEN.. DROPPING")
            dataframe.drop_duplicates(inplace=True)

        if not isinstance(dataframe.index, DatetimeIndex):
            dataframe["datetime"] = pd.to_datetime(dataframe[index], unit='s', utc=True, origin='unix', errors='raise')
            # switching index to the converted timestamp
            dataframe.set_index("datetime", drop=True, inplace=True)
            dataframe.sort_index(axis=0, inplace=True)
        super(OrderFrame, self).__init__(data=dataframe)

        self.pairs = pairs


    def __repr__(self):
        # TODO : HOWTO do this ?
        return repr(self.dataframe)

    def stitch(self, th: OrderFrame) -> OrderFrame:

        # merging without considereing indexes
        newdf_noidx = self.dataframe.reset_index().merge(th.dataframe.reset_index(), how='outer')

        # dropping duplicates (TODO : better/cleaner merge ?)
        newdf = newdf_noidx.drop_duplicates()

        # building new orderframe (should take care of times and indexing properly)
        new_co = OrderFrame(dataframe=newdf.copy())  # explicit copy to prevent modifying self.

        # REMINDER : immutability interface design.
        return new_co

    # # TODO : one property per type for filtering
    # @property
    # def thing(self):
    #     return
    #

    def __contains__(self, item):
        if isinstance(item, datetime):
            return self.begin < item < self.end
        else:  # delegate to dataframe
            return item in self.dataframe

    def __getitem__(self, item: typing.Union[AssetPair, typing.List[AssetPair], datetime, slice, str]):
        if isinstance(item, AssetPair):
            return OrderFrame(
                dataframe = self.dataframe.loc[self.dataframe['pair'] == item.restname],
                pairs=item)
        elif isinstance(item, list):
            return OrderFrame(
                dataframe = self.dataframe.loc[self.dataframe['pair'].isin(i.restname for i in item)],
                pairs=item)
        elif isinstance(item, slice):
            return OrderFrame(
                dataframe = self.dataframe[item],  # let dataframe manage time slices
                pairs=self.pairs)
        elif isinstance(item, (datetime, str)):
            # use usual access via key/index, as for a mapping over time...
            return KClosedOrderModel(**self.dataframe.loc[item])
        else:
            raise KeyError(f"{item} not found")

    def __iter__(self):
        for ts, s in self.dataframe.iterrows():
            yield {idx: KClosedOrderModel(datetime=ts, **s[idx]) for idx in s.index.levels[0]}

    def __len__(self):
        return len(self.dataframe)


def flatten_orderdict(dict_data):
    """we want to flatten multiple dict levels here.
    it is called with nested dict data first -> flattening happens on the way out and needs only 2 levels.
    """
    flatten = dict()
    for k, v in dict_data:  # args is a list of 2-tuples
        if isinstance(v, dict):
            flatten.update({
                k + '_' + vk: vv for vk, vv in v.items()
            })
        else:
            flatten.update({
                k: v
            })

    return flatten


def closedorderframe(closedorders_as_dict: typing.Dict[str, KClosedOrderModel]) -> Result[OrderFrame]:

    if not closedorders_as_dict:
        # TODO :we probably want to expand descr to multiple columns here as well...
        df = pd.DataFrame(columns=[f.name for f in dataclasses.fields(KClosedOrderModel)])  # we only know about index name
    else:
        # Note we drop the key (should already be replicated in the value)
        df = pd.DataFrame.from_records(data=[dataclasses.asdict(v, dict_factory=flatten_orderdict) for v in closedorders_as_dict.values()])

    return Ok(OrderFrame(dataframe=df, index='closetm'))


def openorderframe(openorders_as_dict: typing.Dict[str, KOpenOrderModel]) -> Result[OrderFrame]:

    if not openorders_as_dict:
        # TODO :we probably want to expand descr to multiple columns here as well...
        df = pd.DataFrame(columns=[f.name for f in dataclasses.fields(KOpenOrderModel)])  # we only know about index name
    else:
        # Note we drop the key (should already be replicated in the value)
        df = pd.DataFrame.from_records(data=[dataclasses.asdict(v, dict_factory=flatten_orderdict) for v in openorders_as_dict.values()])

    return Ok(OrderFrame(dataframe=df, index='opentm'))


if __name__ == '__main__':
    pass  # EXAMPLE TODO