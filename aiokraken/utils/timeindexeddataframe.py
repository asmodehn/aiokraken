from __future__ import annotations

import asyncio
import datetime
import functools
import time

import pandas as pd
import numpy as np
import typing
from pandas.api.types import is_numeric_dtype, is_datetime64_dtype


class TimeindexedDataframe:

    """
    A (local) time indexed dataframe.
    This behaves as a directed container (see Danel Ahman papers) for "timeindexed" dataframes.
    It is a central concept in aiokraken.
    """

    dataframe: pd.DataFrame

    def __init__(
        self,
        data: dataframe,
        time_colname: typing.Optional[str] = "time",  # TODO: in metaclass or decorator
        datetime_colname: typing.Optional[str] = "datetime",  # TODO: in metaclass or decorator...
        timer: typing.Callable = functools.partial(datetime.datetime.now, tz=datetime.timezone.utc),  # Maybe more part of hte contect than the dataframe ?
        sleeper: typing.Callable = asyncio.sleep,  # Maybe more part of the context than dataframe ?
    ):
        """
        Dataframe instantiation with explicit time index and datetime human readable equivalent.
        Pass None to prevent either of these column to exist.
        :param data:
        :param time_colname:
        :param datetime_colname:
        """
        if time_colname is not None:
            if not time_colname in data.columns:
                if datetime_colname is not None:
                    # TODO : log
                    # convert datetime series into time
                    # Note :priority is given to date time (more structured) !
                    data[time_colname] = data[datetime_colname].map(
                        lambda dt: dt.timestamp()
                    )
            try:
                # attempt conversion in any case to keep dtypes consistent...
                # NOT WORKING: why ?
                # data[time_colname] = pd.to_numeric(
                #     data[time_colname], downcast="unsigned"
                # )
                # TMP: quickfix
                data[time_colname] = data[time_colname].apply(lambda v: int(v))
            except Exception as e:
                raise

        if datetime_colname is not None:
            if not datetime_colname in data.columns:
                if time_colname is not None:
                    # TODO: log
                    # convert time series into datetime, assuming seconds as unit and UTC as timezone (usual unambiguous Unix server setup)
                    data[datetime_colname] = pd.to_datetime(
                        data[time_colname], utc=True, unit="s"
                    )
            try:
                # attempt conversion in any case to keep dtypes consistent...
                data[datetime_colname] = pd.to_datetime(
                    data[datetime_colname], utc=True, unit="s"
                )
            except Exception as e:
                raise

        self.time_colname = time_colname
        self.datetime_colname = datetime_colname

        self.timer = timer
        self.sleeper = sleeper

        # we index on time (simpler dtype)
        self.dataframe = data.set_index(time_colname)

    def _row_stitcher(self, row: pd.Series, origin_df):

        # retrieving the index by matching time
        rows = origin_df.loc[origin_df[self.time_colname] == row[self.time_colname]]

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
            .set_index("time")
        )

        return TimeindexedDataframe(data=newdf)

    # def collapse(self, timeframe):
    #     # TODO return an collapsed aggregated dataframe...
    #     raise NotImplementedError
    #
    # def expand(self, timeframe):
    #     # TODO return an expanded stretched dataframe...
    #     # LATER : need data distribution & probabilities for stretching, etc.
    #     raise NotImplementedError

    # def __getitem__(self, item):
    #     # Here we have to try guessing the user intent...
    #     # Note : this is always dependent on the precision of the dataframe
    #     if isinstance(
    #         item, int
    #     ):  # assuming time() semantics # TODO : use pint and units to avoid ambiguity...
    #         return self.dataframe[self.dataframe.loc[self.time_colname] == item]
    #     elif isinstance(
    #         item, datetime.time
    #     ):
    #         return self.dataframe[self.dataframe.loc[self.datetime_colname].time() == item]
    #     elif isinstance(
    #         item, datetime.date
    #     ):
    #         return self.dataframe[self.dataframe.loc[self.datetime_colname].date() == item]
    #     elif isinstance(
    #         item, datetime.datetime
    #     ):
    #         return self.dataframe[self.dataframe.loc[self.datetime_colname] == item]

    async def __aiter__(self):
        """
        An iterator on the dataframe, bound in (realworld) time.
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


if __name__ == "__main__":
    now = time.time()
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
            print(f"{time.time()} : {d}")

    asyncio.run(consume())
    # second time will be speedy (time passed already)
    asyncio.run(consume())
