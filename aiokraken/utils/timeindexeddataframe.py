from __future__ import annotations

import asyncio
from datetime import datetime, date, time, timezone
import functools

import pandas as pd
import numpy as np
import typing
from pandas.api.types import is_numeric_dtype, is_datetime64_dtype


class IntLocator:
    def __init__(self, tidf: TimeindexedDataframe):
        self.dataframe = tidf.dataframe

    def __getitem__(self, item: int):
        # TODO : slice case
        return self.dataframe.iloc[item]


class TimeLocator:
    def __init__(self, tidf: TimeindexedDataframe):
        self.dataframe = tidf.dataframe

    def __getitem__(self, item: int):
        # TODO : slice case
        dt = datetime.fromtimestamp(item, tz=timezone.utc)
        return self.dataframe[dt]

# Note : stupid name idea if this ever makes it into his own package : Ailuridae
# It s probably doomed anyway. Just a matter of time.


class TimeindexedDataframe:

    """
    A (local) time indexed dataframe.
    This (should) behave as a directed container (see Danel Ahman papers) for "timeindexed" dataframes.
    For more insight on how to see dataframe as categories, see Spivak's book: Category Theory for Scientists
    It is a central concept in aiokraken.
    """

    # : A Dataframe, indexed on datetime.
    dataframe: pd.DataFrame
    timer: typing.Callable
    sleeper: typing.Callable
    index_name: str

    def __init__(
        self,
        data: dataframe = pd.DataFrame(columns=["datetime"]),
        index: typing.Optional[str] = "datetime",
        timer: typing.Callable = functools.partial(datetime.now, tz=timezone.utc),  # Maybe more part of hte contect than the dataframe ?
        sleeper: typing.Callable = asyncio.sleep,  # Maybe more part of the context than dataframe ?
    ):
        """
        Dataframe instantiation with explicit time index and datetime human readable equivalent.
        Pass None to prevent either of these column to exist.
        :param data:
        :param time_colname:
        :param datetime_colname:
        """
        self.timer = timer
        self.sleeper = sleeper

        self.dataframe = data.copy(deep=True)  # copy to not modify origin (immutable semantics for generic dataframes)
        # TODO : maybe manage that with contracts instead ?
        if not isinstance(self.dataframe.index, pd.DatetimeIndex):
            if index in self.dataframe.columns:
                self.dataframe.set_index(index, inplace=True)
            else:  # create it and timestamp it
                self.dataframe[index] = datetime.now(tz=timezone.utc)
                self.dataframe.set_index(index, inplace=True)

            self.dataframe.index = pd.to_datetime(self.dataframe.index)
        # else the index is already a datetime, everything is fine.

        # TODO : maybe we dont really need this one ? already stored in dataframe at df.index.name...
        #  only useful for stitcher, for now
        self.index_name = self.dataframe.index.name

    def _row_stitcher(self, row: pd.Series, origin_df):

        # retrieving the index by matching time
        rows = origin_df.loc[origin_df[self.index_name] == row[self.index_name]]

        if len(rows) > 1:
            # default merge strategy : last one wins
            row = rows.iloc[-1]

        return row

    def __call__(self, tidf: TimeindexedDataframe):

        newdf_noidx = self.dataframe.reset_index().merge(
            tidf.dataframe.reset_index(), how="outer", sort=True
        )

        newdf = (
            newdf_noidx.agg(
                functools.partial(self._row_stitcher, origin_df=newdf_noidx), axis=1
            )
            .drop_duplicates()
            .set_index(self.index_name)
        )
        # REMEMBER : immutable functional semantics here...
        return TimeindexedDataframe(data=newdf)

    # def collapse(self, timeframe):
    #     # TODO return an collapsed aggregated dataframe...
    #     raise NotImplementedError
    #
    # def expand(self, timeframe):
    #     # TODO return an expanded stretched dataframe...
    #     # LATER : need data distribution & probabilities for stretching, etc.
    #     raise NotImplementedError


    @property
    def iloc(self):
        """
        Intent : mimic pandas integer locator. useful for known offset access (first, last, etc.)
        :return:
        """
        return IntLocator(self)

    @property
    def tloc(self):
        """
        Intent: (unix) time based accessor. works also on slices.
        LATER: If time as a pint unit, same behavior as man datetime index locator
        :return:
        """
        return TimeLocator(self)

    # ref : https://stackoverflow.com/questions/16033017/how-to-override-the-slice-functionality-of-list-in-its-derived-class
    def __getitem__(self, item: typing.Union[slice, datetime, date, time, str]):  # TODO : deal with slices as well !!
        # TODO : note  this can be used as a filter... on time or other...
        # Here we have to try guessing the user intent...
        # Note : this is always dependent on the precision of the dataframe
        # TODO: probably we want to match the semantics of pandas for this
        if isinstance(item, datetime):
            subdata = self.dataframe[self.dataframe[self.index_name] == item]
        elif isinstance(item, date):
            subdata = self.dataframe[self.dataframe[self.index_name].date() == item]
        elif isinstance(item, time):  # CAREFUL This gives a daily dataframe
            subdata = self.dataframe[self.dataframe[self.index_name].time() == item]
        else:  # we dont know just try something (the general pandas case)
            subdata = self.dataframe[item]

        return TimeindexedDataframe(
            data=subdata,
            timer=self.timer,
            sleeper=self.sleeper
        )

    async def __aiter__(self):
        """
        An iterator on the dataframe, bound in (realworld) time.
        Note : This is linear :
          Calling iter multiple time will duplicate the data source, and start again from the beginning.
        :return:
        """
        # new iter call always start at the beginning
        pointer_loc = 0

        # We are tied to external time flow.
        while pointer_loc < len(self.dataframe):  # since time index is ordered
            next_pointer = self.dataframe.index[pointer_loc]

            now = self.timer()
            if next_pointer > now.timestamp():
                # we sleep to wait for the next present. we are prevented from going into the future.
                await self.sleeper((next_pointer - now.timestamp()))

            yield self.dataframe.loc[next_pointer]

            # points to next :
            pointer_loc += 1

    def __len__(self):
        return len(self.dataframe)

    def __copy__(self):
        return TimeindexedDataframe(data=self.dataframe.copy(), timer=self.timer, sleeper=self.sleeper, index=self.index_name)

    def __mul__(self, other: TimeindexedDataframe):  # categorical product : merging columns

        # we merge on index (datetime)
        # TODO : think about merging different timeframes... ok or not ?
        merged_df = pd.merge(self.dataframe, other.dataframe, right_index=True, left_index=True)

        # TODO : semantics ? copy or ref ?
        return TimeindexedDataframe(data=merged_df, timer=self.timer, sleeper=self.sleeper)


if __name__ == "__main__":

    from time import time as unixtime
    now = unixtime()
    tidf = TimeindexedDataframe(data=pd.DataFrame(
                    [
                        [
                            now,
                            1,
                        ],
                        [
                            now + 5,  # five secs later
                            5,
                        ],
                        [
                            now + 10,  # ten secs later
                            10,
                        ],
                    ],
                    # grab that from kraken documentation
                    columns=[
                        "time",
                        "number"
                    ],
                ),
    )

    async def consume():
        global tidf
        async for d in tidf:
            print(f"{unixtime()} : {d}")

    asyncio.run(consume())
    # second time will be speedy (time passed already)
    asyncio.run(consume())