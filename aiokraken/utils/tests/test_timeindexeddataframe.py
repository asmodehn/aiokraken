import unittest
from datetime import datetime, timezone

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

        stitched1 = tidf1(tidf2)

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

        assert ptypes.is_datetime64_any_dtype(tidf.dataframe["datetime"])
        assert tidf.dataframe.index.name == "time"
        assert tidf.dataframe.index.dtype == "int64"

        # verifying all ways to access data
        firstdatetime = datetime(
            year=2019, month=8, day=29, hour=0, minute=47, second=0, tzinfo=timezone.utc
        )
        # get the first element
        assert isinstance(tidf.iloc[0], pd.Series)
        assert tidf.iloc[0]["datetime"] == firstdatetime

        # get based on timeindex
        assert isinstance(tidf.tloc[1567039620], pd.Series)
        assert tidf.tloc[1567039620]["datetime"] == firstdatetime

        # get from datetime
        assert isinstance(tidf[firstdatetime], pd.Series)
        assert tidf[firstdatetime]["datetime"] == firstdatetime

        scnddatetime = datetime(
            year=2019, month=8, day=29, hour=0, minute=48, second=0, tzinfo=timezone.utc
        )

        # get slice
        assert isinstance(tidf[firstdatetime:scnddatetime], TimeindexedDataframe)
        assert tidf[firstdatetime].iloc[0]["datetime"] == firstdatetime


    def test_iter_ok(self):

        raise NotImplementedError




if __name__ == "__main__":
    unittest.main()
