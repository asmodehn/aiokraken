import unittest
from datetime import datetime, timezone

from pandas import DatetimeTZDtype
from parameterized import parameterized
import pandas as pd

from aiokraken.utils.timeindexeddataframe import TimeindexedDataframe

"""
Test module.
This is intended for extensive testing, using parameterized, hypothesis or similar generation methods
For simple usecase examples, we should rely on doctests.
"""


class TestTimeindexedDataframe(unittest.TestCase):
    @parameterized.expand(
        [
            [
                pd.DataFrame(  # One with "datetime" column (like internal model)
                    # TODO: proper currencies...
                    [
                        [
                            datetime.fromtimestamp(1567039620, tz=timezone.utc),
                            8746.4,
                            8751.5,
                            8745.7,
                            8745.7,
                            8749.3,
                            0.09663298,
                            8,
                        ],
                        [
                            datetime.fromtimestamp(1567039680, tz=timezone.utc),
                            8745.7,
                            8747.3,
                            8745.7,
                            8747.3,
                            8747.3,
                            0.00929540,
                            1,
                        ],
                    ],
                    # grab that from kraken documentation
                    columns=[
                        "datetime",
                        "open",
                        "high",
                        "low",
                        "close",
                        "vwap",
                        "volume",
                        "count",
                    ],
                )  # there is no datetime index a priori.
            ], [
                pd.DataFrame(  # One with "datetime" column (like internal model)
                    # TODO: proper currencies...
                    [
                        [
                            datetime.fromtimestamp(1567039620, tz=timezone.utc),
                            8746.4,
                            8751.5,
                            8745.7,
                            8745.7,
                            8749.3,
                            0.09663298,
                            8,
                        ],
                        [
                            datetime.fromtimestamp(1567039680, tz=timezone.utc),
                            8745.7,
                            8747.3,
                            8745.7,
                            8747.3,
                            8747.3,
                            0.00929540,
                            1,
                        ],
                    ],
                    # grab that from kraken documentation
                    columns=[
                        "datetime",
                        "open",
                        "high",
                        "low",
                        "close",
                        "vwap",
                        "volume",
                        "count",
                    ],
                ).set_index("datetime")  # we already have an index
            ],
        ]
    )
    def test_load_ok(self, df):
        """ Verifying that expected data parses properly """
        tidf = TimeindexedDataframe(data=df, index="datetime")

        import pandas.api.types as ptypes

        num_cols = ["open", "high", "low", "close", "vwap", "volume", "count"]
        assert all(ptypes.is_numeric_dtype(tidf.dataframe[col]) for col in num_cols)

        assert tidf.dataframe.index.name == "datetime"
        # Verify we have a timezone aware, ns precision datetime.
        assert ptypes.is_datetime64tz_dtype(tidf.dataframe.index.dtype)
        assert ptypes.is_datetime64_ns_dtype(tidf.dataframe.index.dtype)

    # TODO : property test instead (move this example test to doc...)

    @parameterized.expand(
        [
            [
                pd.DataFrame(
                    # TODO:   proper Time, proper currencies...
                    [
                        [
                            datetime.fromtimestamp(1567039620, tz=timezone.utc),
                            8746.4,
                            8751.5,
                            8745.7,
                            8745.7,
                            8749.3,
                            0.09663298,
                            8,
                        ],
                        [
                            datetime.fromtimestamp(1567039680, tz=timezone.utc),
                            8745.7,
                            8747.3,
                            8745.7,
                            8747.3,
                            8747.3,
                            0.00929540,
                            1,
                        ],
                    ],
                    # grab that from kraken documentation
                    columns=[
                        "datetime",
                        "open",
                        "high",
                        "low",
                        "close",
                        "vwap",
                        "volume",
                        "count",
                    ],
                ),
                pd.DataFrame(
                    # TODO:   proper Time, proper currencies...
                    [
                        [
                            datetime.fromtimestamp(1567039680, tz=timezone.utc),
                            8745.8,
                            8747.3,
                            8745.7,
                            8747.3,
                            8747.3,
                            0.00929540,
                            1,
                        ],  # Not the value is a bit modified to trigger stitching...
                        [
                            datetime.fromtimestamp(1567039720, tz=timezone.utc),
                            8746.6,
                            8751.4,
                            8745.3,
                            8745.4,
                            8748.1,
                            0.09663297,
                            3,
                        ],
                    ],
                    # grab that from kraken documentation
                    columns=[
                        "datetime",
                        "open",
                        "high",
                        "low",
                        "close",
                        "vwap",
                        "volume",
                        "count",
                    ],
                ),
            ],
        ]
    )
    def test_stitch_ok(
        self, df1, df2
    ):  # TODO : there are MANY cases to test for stitch
        """ Verifying that expected data parses properly """
        tidf1 = TimeindexedDataframe(data=df1)
        tidf2 = TimeindexedDataframe(data=df2)

        stitched1 = tidf1.merge(tidf2)

        import pandas.api.types as ptypes

        num_cols = ["open", "high", "low", "close", "vwap", "volume", "count"]
        assert all(
            ptypes.is_numeric_dtype(stitched1.dataframe[col]) for col in num_cols
        )

        assert stitched1.dataframe.index.name == "datetime"
        # Verify we have a timezone aware, ns precision datetime.
        assert ptypes.is_datetime64tz_dtype(stitched1.dataframe.index.dtype)
        assert ptypes.is_datetime64_ns_dtype(stitched1.dataframe.index.dtype)

        # verifying stitches
        assert (stitched1.dataframe.iloc[0] == tidf1.dataframe.iloc[0]).all()
        assert (stitched1.dataframe.iloc[-1] == tidf2.dataframe.iloc[-1]).all()

        assert len(stitched1) == 3

        # Note : careful with default merging strategy, ORDER MATTERS !
        # To make it not matter, we need mode semantics...

    @parameterized.expand(
        [
            [
                pd.DataFrame(  # One with "datetime" column (like internal model)
                    # TODO:   proper Time, proper currencies...
                    [
                        [
                            datetime.fromtimestamp(1567039620, tz=timezone.utc),
                            8746.4,
                            8751.5,
                            8745.7,
                            8745.7,
                            8749.3,
                            0.09663298,
                            8,
                        ],
                        [
                            datetime.fromtimestamp(1567039680, tz=timezone.utc),
                            8745.7,
                            8747.3,
                            8745.7,
                            8747.3,
                            8747.3,
                            0.00929540,
                            1,
                        ],
                    ],
                    # grab that from kraken documentation
                    columns=[
                        "datetime",
                        "open",
                        "high",
                        "low",
                        "close",
                        "vwap",
                        "volume",
                        "count",
                    ],
                ).set_index("datetime")
            ],
        ]
    )
    def test_getitem_ok(self, df):
        """ Verifying that expected data parses properly """
        tidf = TimeindexedDataframe(data=df)

        import pandas.api.types as ptypes

        num_cols = ["open", "high", "low", "close", "vwap", "volume", "count"]
        assert all(ptypes.is_numeric_dtype(tidf.dataframe[col]) for col in num_cols)

        assert ptypes.is_datetime64_any_dtype(tidf.dataframe.index)
        assert tidf.dataframe.index.name == "datetime"
        assert tidf.dataframe.index.dtype == DatetimeTZDtype(tz=timezone.utc)

        # verifying all ways to access data

        # get the first element
        assert isinstance(tidf.iloc[0], pd.Series)
        assert tidf.iloc[0]["open"] == 8746.4
        assert tidf.iloc[0]["high"] == 8751.5
        assert tidf.iloc[0]["low"] == 8745.7
        assert tidf.iloc[0]["close"] == 8745.7
        assert tidf.iloc[0]["vwap"] == 8749.3
        assert tidf.iloc[0]["volume"] == 0.09663298
        assert tidf.iloc[0]["count"] == 8

        # NOT WORKING
        # get based on timeindex
        # assert isinstance(tidf.tloc[1567039620], pd.Series)
        # assert tidf.tloc[1567039620]["open"] == 8746.4
        # assert tidf.tloc[1567039620]["high"] == 8751.5
        # assert tidf.tloc[1567039620]["low"] == 8745.7
        # assert tidf.tloc[1567039620]["close"] == 8745.7
        # assert tidf.tloc[1567039620]["vwap"] == 8749.3
        # assert tidf.tloc[1567039620]["volume"] == 0.09663298
        # assert tidf.tloc[1567039620]["count"] == 8

        # get from datetime
        firstdatetime = datetime(
            year=2019, month=8, day=29, hour=0, minute=47, second=0, tzinfo=timezone.utc
        )
        assert isinstance(tidf[firstdatetime], pd.Series)
        assert tidf[firstdatetime]["open"] == 8746.4
        assert tidf[firstdatetime]["high"] == 8751.5
        assert tidf[firstdatetime]["low"] == 8745.7
        assert tidf[firstdatetime]["close"] == 8745.7
        assert tidf[firstdatetime]["vwap"] == 8749.3
        assert tidf[firstdatetime]["volume"] == 0.09663298
        assert tidf[firstdatetime]["count"] == 8

        scnddatetime = datetime(
            year=2019, month=8, day=29, hour=0, minute=48, second=0, tzinfo=timezone.utc
        )

        # get slice and verify equality
        assert isinstance(tidf[firstdatetime:scnddatetime], TimeindexedDataframe)
        assert tidf[firstdatetime:scnddatetime] == tidf

        # get list of columns only
        assert isinstance(tidf[["open", "high", "low", "close"]], TimeindexedDataframe)
        assert tidf[["open", "high", "low", "close"]][firstdatetime]["open"] == tidf[firstdatetime]["open"]
        assert tidf[["open", "high", "low", "close"]][firstdatetime]["high"] == tidf[firstdatetime]["high"]
        assert tidf[["open", "high", "low", "close"]][firstdatetime]["low"] == tidf[firstdatetime]["low"]
        assert tidf[["open", "high", "low", "close"]][firstdatetime]["close"] == tidf[firstdatetime]["close"]


    @parameterized.expand(
        [
            [
                pd.DataFrame(  # One with "datetime" column (like internal model)
                    # TODO:   proper Time, proper currencies...
                    [
                        [
                            datetime.fromtimestamp(1567039620, tz=timezone.utc),
                            8746.4,
                            8751.5,
                            8745.7,
                            8745.7,
                            8749.3,
                            0.09663298,
                            8,
                        ],
                        [
                            datetime.fromtimestamp(1567039680, tz=timezone.utc),
                            8745.7,
                            8747.3,
                            8745.7,
                            8747.3,
                            8747.3,
                            0.00929540,
                            1,
                        ],
                    ],
                    # grab that from kraken documentation
                    columns=[
                        "datetime",
                        "open",
                        "high",
                        "low",
                        "close",
                        "vwap",
                        "volume",
                        "count",
                    ],
                ).set_index("datetime")
            ],
        ]
    )
    def test_iter_ok(self, df):
        """ Verifying that expected data parses properly """
        tidf = TimeindexedDataframe(data=df)

        import pandas.api.types as ptypes

        num_cols = ["open", "high", "low", "close", "vwap", "volume", "count"]
        assert all(ptypes.is_numeric_dtype(tidf.dataframe[col]) for col in num_cols)

        assert ptypes.is_datetime64_any_dtype(tidf.dataframe.index)
        assert tidf.dataframe.index.name == "datetime"
        assert tidf.dataframe.index.dtype == DatetimeTZDtype(tz=timezone.utc)

        it = iter(tidf)
        ts, s = next(it)
        assert ts == datetime(
            year=2019, month=8, day=29, hour=0, minute=48, second=0, tzinfo=timezone.utc
        )
        assert (s == pd.Series(data={
            "open":8745.7,
            "high":8747.3,
            "low":8745.7,
            "close":8747.3,
            "vwap":8747.3,
            "volume":0.00929540,
            "count":1,
        })).all()

        ts2, s2 = next(it)
        assert ts2 == datetime(
            year=2019, month=8, day=29, hour=0, minute=47, second=0, tzinfo=timezone.utc
        )
        assert (s2 == pd.Series(data={
            "open": 8746.4,
            "high": 8751.5,
            "low": 8745.7,
            "close": 8745.7,
            "vwap": 8749.3,
            "volume": 0.09663298,
            "count": 8,
        })).all()


    def test_aiter_ok(self):
        raise NotImplementedError




if __name__ == "__main__":
    unittest.main()
