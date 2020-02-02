from __future__ import annotations

import functools

import pandas as pd
import numpy as np
import typing
from pandas.api.types import is_numeric_dtype, is_datetime64_dtype


class TimeindexedDataframe:

    # Ref: https://pandas.pydata.org/pandas-docs/stable/development/extending.html

    """
    A (local) time indexed dataframe.
    This behaves as a directed container (see Danel Ahman papers) for "timeindexed" dataframes.
    It is a central concept in aiokraken.
    """

    dataframe: pd.DataFrame

    def __init__(
        self,
        data: dataframe,
        time_colname: typing.Optional[str] = "time",
        datetime_colname: typing.Optional[str] = "datetime",
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
                data[time_colname] = pd.to_numeric(
                    data[time_colname], downcast="unsigned"
                )
            except Exception as e:
                raise

        if datetime_colname is not None:
            if not datetime_colname in data.columns:
                if time_colname is not None:
                    # TODO: log
                    # convert time series into datetime, assuming seconds as unit and UTC as timezone (usual unambiguous Unix server setup)
                    data[datetime_colname] = pd.to_datetime(
                        data.time, utc=True, unit="s"
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

    def __getitem__(self, item):
        if isinstance(
            item, int
        ):  # assuming time # TODO : use pint and units to avoid ambiguity...
            pass

    def __iter__(self):
        raise NotImplementedError

    def __next__(self):
        raise NotImplementedError

    def __len__(self):
        return len(self.dataframe)


if __name__ == "__main__":
    pass
